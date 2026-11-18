# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
import hashlib
import json
import re

from genlayer import *


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def source_url(ref):
    if len(ref) > 200 or not re.fullmatch(
        r"[A-Za-z0-9][A-Za-z0-9-]*/[A-Za-z0-9_.-]+/[a-f0-9]{40}/(?:[A-Za-z0-9_-]+/)*[A-Za-z0-9_-]+\.json",
        ref,
    ) or ref.split("/")[1] in (".", ".."):
        raise ValueError("Invalid source")
    return "https://raw.githubusercontent.com/" + ref


def unique_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON key")
        result[key] = value
    return result


def register_value(value):
    return type(value) is int and 0 <= value <= 0xFFFFFFFF


def identifier(value):
    return type(value) is str and re.fullmatch(r"[A-Za-z0-9_-]{1,24}", value) is not None


def parse_trace(body, commitment):
    if len(body) > 8192 or sha256(body) != commitment:
        raise ValueError("Trace commitment mismatch")
    document = json.loads(body.decode("utf-8"), object_pairs_hook=unique_keys)
    if type(document) is not dict or set(document) != {"initial", "events"}:
        raise ValueError("Invalid trace schema")
    events = document["events"]
    initial = document["initial"]
    if not register_value(initial) or type(events) is not list or not 2 <= len(events) <= 16:
        raise ValueError("Expected an initial u32 and one to eight complete operations")

    operations = {}
    active_clients = set()
    arity = {"read": 0, "write": 1, "cas": 2}
    for tick, event in enumerate(events):
        if type(event) is not list or len(event) < 3 or not identifier(event[1]):
            raise ValueError("Malformed event")
        kind, operation_id = event[:2]
        if kind == "call":
            if len(event) < 4:
                raise ValueError("Malformed invocation")
            client, method, *args = event[2:]
            if not identifier(client) or client in active_clients or operation_id in operations:
                raise ValueError("Concurrent calls by one client or repeated invocation ID")
            if type(method) is not str or arity.get(method) != len(args) or not all(map(register_value, args)):
                raise ValueError("Invalid method arguments")
            active_clients.add(client)
            operations[operation_id] = {"id": operation_id, "client": client, "method": method,
                                        "args": args, "call": tick}
        elif kind == "return":
            operation = operations.get(operation_id)
            if len(event) != 3 or operation is None or "return" in operation:
                raise ValueError("Response lacks a matching pending invocation")
            result = event[2]
            method = operation["method"]
            valid = {"read": register_value(result), "write": result is None, "cas": type(result) is bool}
            if not valid[method]:
                raise ValueError("Invalid method response")
            operation["result"] = result
            operation["return"] = tick
            active_clients.remove(operation["client"])
        else:
            raise ValueError("Unknown event type")
    if active_clients:
        raise ValueError("Incomplete trace")
    return initial, list(operations.values())


def apply_operation(operation, value):
    method = operation["method"]
    result = operation["result"]
    args = operation["args"]
    if method == "read":
        return value if result == value else None
    if method == "write":
        return args[0]
    matches = value == args[0]
    if result != matches:
        return None
    return args[1] if matches else value


def enumerate_outcomes(initial, operations):
    count = len(operations)
    predecessors = [
        sum(1 << i for i, other in enumerate(operations) if other["return"] < op["call"])
        for op in operations
    ]
    # Equivalent prefixes end at the same completed operation set and value.
    frontier = {(0, initial): ()}
    for _ in operations:
        following = {}
        for (done, value), order in frontier.items():
            for i, operation in enumerate(operations):
                bit = 1 << i
                if done & bit or predecessors[i] & ~done:
                    continue
                next_value = apply_operation(operation, value)
                if next_value is not None:
                    following.setdefault((done | bit, next_value), order + (i,))
        if not following:
            deepest = next(iter(frontier.values()))
            return {"status": "INCONSISTENT", "terminals": [],
                    "deepest_prefix": [operations[i]["id"] for i in deepest]}
        frontier = following

    terminals = [
        {"value": value, "order": [operations[i]["id"] for i in order]}
        for (_, value), order in sorted(frontier.items())
    ]
    return {"status": "DETERMINATE" if len(terminals) == 1 else "AMBIGUOUS",
            "terminals": terminals}


class RegisterTraceWitness(gl.Contract):
    reports: TreeMap[str, str]

    def __init__(self):
        pass

    @gl.public.write
    def check_history(self, coordinate: str, expected_sha256: str) -> str:
        if not re.fullmatch(r"[0-9a-f]{64}", expected_sha256):
            raise gl.vm.UserError("Expected exact trace SHA-256")
        try:
            url = source_url(coordinate)
        except ValueError:
            raise gl.vm.UserError("Expected a commit-pinned trace")

        def observe():
            try:
                response = gl.nondet.web.get(url)
                if response.status == 200:
                    initial, operations = parse_trace(response.body, expected_sha256)
                    return canonical({
                        "schema": "register-trace-witness/1", "source_url": url,
                        "source_sha256": expected_sha256, "initial": initial, "operations": operations,
                        "outcome": enumerate_outcomes(initial, operations),
                    })
            except Exception:
                raise gl.vm.UserError("Trace unavailable or invalid")
            raise gl.vm.UserError("Trace unavailable or invalid")

        def validate(leader):
            if not isinstance(leader, gl.vm.Return):
                return False
            try:
                return observe() == leader.calldata
            except Exception:
                return False

        report = gl.vm.run_nondet_unsafe(observe, validate)
        handle = sha256(report.encode("ascii"))
        if handle not in self.reports:
            self.reports[handle] = report
        return handle

    @gl.public.view
    def get_report(self, handle: str) -> dict:
        if handle not in self.reports:
            raise gl.vm.UserError("Unknown history report")
        return json.loads(self.reports[handle])

    @gl.public.view
    def continuation_value(self, handle: str) -> u32:
        outcome = self.get_report(handle)["outcome"]
        if outcome["status"] != "DETERMINATE":
            raise gl.vm.UserError("History has no unique continuation value")
        return outcome["terminals"][0]["value"]
