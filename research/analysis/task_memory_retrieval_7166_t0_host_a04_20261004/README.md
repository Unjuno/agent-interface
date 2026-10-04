# Task-conditioned GUI memory retrieval T0 — host A04

A04 is a fresh additive successor to the preserved A03 `FAIL_METHOD`. A03's
frozen auditor used a no-op `wrong_label` mutation (NONE changed to NONE), which
escaped detection. A04 tests the same 72-case method contract with a new
auditor that proves each mutation changes raw content before checking rejection.
It does not alter or regrade A03.

Run `build_fixture.py` only before the freeze to create `fixture.json` and the
separate `oracle.json`. `candidate.py` reads only the fixture and writes once to
`results/candidate.json`. After candidate exit 0, `auditor.py` independently
reconstructs expected labels and checks six corrupted-output controls, then
writes `results/audit.json`. No model, GUI, retrieval backend, network, GPU,
container, or input is used. The same-day OrbStack content-store STOP already
recorded in Issue #7383 is not retried; this allocation is explicitly host-only.

`PASS_METHOD_SCOPED` means only that this authored finite contract and six
effective mutation controls pass. It does not establish retrieval utility,
model behavior, token/image cost, task correctness, latency, runtime or product
value. Construction tests are separate from the one-shot candidate and auditor.
