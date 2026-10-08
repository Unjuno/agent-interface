# Task-conditioned GUI memory retrieval T0 — host A03

This is a fresh additive allocation for Issue #7166 after A01's stale-main
STOP and A02's preregistered-but-uninvoked state. It does not alter either
predecessor or claim that A02 ran. The experiment is a deterministic, authored
72-case method fixture. It tests only the finite retrieval-label, provenance,
abstention and no-authority contract.

Run `build_fixture.py` only before the freeze to create `fixture.json` and the
separate `oracle.json`. `candidate.py` reads only the fixture and writes once to
`results/candidate.json`. After candidate exit 0, `auditor.py` independently
reconstructs expected labels and checks six corrupted-output controls, then
writes `results/audit.json`. No model, GUI, retrieval backend, network, GPU,
container, or input is used. The same-day OrbStack content-store STOP already
recorded in Issue #7383 is not retried; this allocation is explicitly host-only.

`PASS_METHOD_SCOPED` means only that this authored finite contract and these
six mutation controls pass. It does not establish retrieval utility, model
behavior, token/image cost, task correctness, latency, runtime or product value.
Construction tests are separate from the one-shot candidate and auditor.
