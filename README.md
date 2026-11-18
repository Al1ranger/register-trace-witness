# RegisterTraceWitness

RegisterTraceWitness reconstructs every possible terminal value of a
single atomic register from a completed concurrent history. It supports reads,
writes, and compare-and-swap (CAS). Given a public trace, it finds a witness
ordering for each possible value or demonstrates that no valid order exists.

Anyone can call `check_history(coordinate, expected_sha256)` with a
commit-pinned GitHub JSON path. The leader and validators independently
fetch the entire trace, check the HTTP result and exact digest, pair
invocations with responses, and recompute the outcome. Agreement covers the
normalized operations, every terminal value, their witness orders, and the
canonical result. The contract stores this report under its content hash.

A completed operation precedes an operation invoked after its response.
Overlapping operations may take effect in either order if the observed read
values and CAS responses permit it. The search merges equivalent prefixes
with the same completed operation set and register value. The
[linearizability specification](https://www.cs.columbia.edu/~wing/publications/HerlihyWing89a.pdf)
describes the sequential and real-time constraints this checker applies.

- `DETERMINATE` means all valid orders give the same terminal value.
- `AMBIGUOUS` means multiple values remain possible, with one witness order per value.
- `INCONSISTENT` means the search found no valid complete order. The report includes an example of a longest valid partial order.

`get_report(handle)` returns the full evidence and result. Consumers can
call `continuation_value(handle)` only for a determinate trace.

The file describes one register with an unsigned 32-bit initial value and
1–8 complete operations. An event array uses a single recorder's order,
unique operation IDs, and at most one pending call per client. See
[the examples](fixtures). The contract checks the published history. Trace
coverage and recorder accuracy depend on the publisher. The fixtures are
synthetic counterexamples and valid traces.

```sh
python -m pip install -r requirements-dev.txt
python -m pytest tests -q
genvm-lint check contracts/RegisterTraceWitness.py
```

[StudioNet proofs](LIVE_PROOFS.md) · [Submission](SUBMISSION.md)

Replay the receipt and state checks without a signer.

```sh
npm ci
node scripts/prove.mjs 12d6ae88200d12daa6bc5f52ef53b5ea24b743b4 --verify-only
```
