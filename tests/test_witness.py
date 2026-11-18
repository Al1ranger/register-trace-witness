import hashlib
import itertools
import json
import re
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
CODE = ROOT / "contracts/RegisterTraceWitness.py"
BASE = "Al1ranger/register-trace-witness/" + "a" * 40 + "/fixtures/"


@pytest.fixture
def witness(direct_deploy):
    contract = direct_deploy(str(CODE))
    return contract, sys.modules[type(contract._instance).__module__]


def body_of(name):
    return (ROOT / "fixtures" / (name + ".json")).read_bytes()


def mock_trace(vm, name, body, status=200):
    coordinate = BASE + name + ".json"
    url = "https://raw.githubusercontent.com/" + coordinate
    vm.mock_web(re.escape(url) + "$", {"method": "GET", "response": {
        "status": status, "headers": {}, "body": body,
    }})
    return coordinate


@pytest.mark.parametrize(("name", "expected"), [
    ("overlap", {"status": "DETERMINATE", "terminals": [
        {"value": 3, "order": ["B", "A", "C", "D", "E", "F"]}]}),
    ("stale-read", {"status": "INCONSISTENT", "terminals": [], "deepest_prefix": ["A", "B"]}),
    ("two-terminals", {"status": "AMBIGUOUS", "terminals": [
        {"value": 1, "order": ["B", "A"]}, {"value": 2, "order": ["A", "B"]}]}),
])
def test_public_witness(witness, direct_vm, name, expected):
    contract, mod = witness
    body = body_of(name)
    commitment = hashlib.sha256(body).hexdigest()
    coordinate = mock_trace(direct_vm, name, body)
    handle = contract.check_history(coordinate, commitment)
    report = contract.get_report(handle)
    assert report["outcome"] == expected
    assert report["source_sha256"] == commitment
    assert mod.sha256(mod.canonical(report).encode("ascii")) == handle
    assert direct_vm.run_validator()
    forgery = dict(report, outcome={"status": "DETERMINATE", "terminals": [{"value": 55, "order": []}]})
    assert not direct_vm.run_validator(leader_result=mod.canonical(forgery))
    assert contract.check_history(coordinate, commitment) == handle
    direct_vm.clear_mocks()
    mock_trace(direct_vm, name, body + b" ")
    assert not direct_vm.run_validator()
    if name == "overlap":
        assert contract.continuation_value(handle) == 3
    else:
        with direct_vm.expect_revert("History has no unique continuation value"):
            contract.continuation_value(handle)


def brute_force(initial, operations):
    endpoints = set()
    orders = set()
    for order in itertools.permutations(operations):
        if any(earlier["call"] > later["return"]
               for i, earlier in enumerate(order) for later in order[i + 1:]):
            continue
        value = initial
        for op in order:
            match op["method"]:
                case "write":
                    value = op["args"][0]
                case "read":
                    if value != op["result"]:
                        break
                case "cas":
                    expected, new = op["args"]
                    if (value == expected) != op["result"]:
                        break
                    if value == expected:
                        value = new
        else:
            endpoints.add(value)
            orders.add((value, tuple(op["id"] for op in order)))
    return endpoints, orders


def test_search_matches_permutations(witness):
    _, mod = witness
    # Vary read and CAS observations independently across overlapping intervals.
    for first_read, second_read, succeeded, initial in itertools.product(range(4), range(4), (True, False), range(3)):
        events = {"initial": initial, "events": [
            ["call", "A", "a", "write", 1],
            ["call", "B", "b", "read"],
            ["call", "C", "c", "cas", 1, 2],
            ["return", "B", first_read],
            ["return", "A", None],
            ["call", "D", "a", "read"],
            ["return", "C", succeeded],
            ["return", "D", second_read],
        ]}
        body = json.dumps(events).encode()
        _, ops = mod.parse_trace(body, mod.sha256(body))
        expected_values, legal_witnesses = brute_force(initial, ops)
        report = mod.enumerate_outcomes(initial, ops)
        assert {entry["value"] for entry in report["terminals"]} == expected_values
        assert all((entry["value"], tuple(entry["order"])) in legal_witnesses for entry in report["terminals"])
        assert (report["status"] == "INCONSISTENT") == (not expected_values)


@pytest.mark.parametrize("events", [
    [["call", "A", "a", "read"], ["return", "A", True]],
    [["call", "A", "a", "read"], ["return", "B", 0]],
    [["call", "A", "a", "read"], ["call", "B", "a", "read"]],
    [["call", "A", "a", "write", 1], ["return", "A", 1]],
    [["call", "A", "a", "cas", 0, 1], ["return", "A", 1]],
    [["call", "A", "a", "cas", 0, 4294967296], ["return", "A", False]],
])
def test_malformed_trace_rejected(witness, events):
    _, mod = witness
    body = json.dumps({"initial": 0, "events": events}).encode()
    with pytest.raises(ValueError):
        mod.parse_trace(body, mod.sha256(body))


def test_http_error_reverts(witness, direct_vm):
    contract, _ = witness
    body = body_of("overlap")
    coordinate = mock_trace(direct_vm, "overlap", body, status=404)
    with direct_vm.expect_revert("Trace unavailable or invalid"):
        contract.check_history(coordinate, hashlib.sha256(body).hexdigest())
