# V39 active observation frame integrity A02

Disposition: `PASS_CONSTRUCTION_ONLY`. Parent issue: [#59](https://github.com/Unjuno/agent-interface/issues/59).

This additive run audits the active-frame integrity repair at PR #7965 tip `9923f5a643b4ccc3354c94b84e533bfe0441807a`. Delivery requires `exact is True`, validates that the paired soft event and observation refer to the same RGB digest, decodes the PNG bytes read from disk and compares the pixels with that digest, then sends those same PNG bytes. The receipt records both PNG-byte and validated RGB hashes.

The production nested-wait tests exercise a valid exact frame and verify that a same-sequence PNG replaced after monitor acceptance is rejected before planner delivery. Additional focused tests cover planner adapter composition, App Server client, paired V39 signal handling, controller behavior, and pair dispatch.

## H/T/D/C/U

- **H:** At the active-turn composition boundary, only a matching exact frame can accompany its paired soft event to the current planner turn.
- **T:** Run the six focused suites and compile the three runtime modules; preserve raw outputs and exit codes.
- **D:** PASS when counts match the frozen expected suite counts, all suites and compile pass, and an independent audit checks source hashes.
- **C:** This confirms deterministic source composition and artifact identity. App Server acceptance represents queued untrusted context; it does not demonstrate model comprehension or behavior. Timeout ambiguity is handled by the existing invalidation route.
- **U:** No model inference, live game, GUI, OS input, physical release, useful feedback, recovery, latency/cost comparison, or task effect was measured. Live V39 remains unassigned.

## Frozen run

- Exact tested PR head: `9923f5a643b4ccc3354c94b84e533bfe0441807a`.
- Runtime interpreter: Windows CPython 3.11.9.
- Six suites: planner adapter 12, App Server client 4, paired signal 21, controller 5, nested wait 10, pair dispatch 1; total 53.
- Python compilation of App Server client, planner adapter, and V39 controller passed.
- Frozen source SHA-256:
- `research/doom/map01_overlap_controller_v39.py`: `6b3fbf2fe651557a3178a33cbf1ba0145ba5145a54c57b1c8db42252957f4d8f`
- `research/doom/test_map01_overlap_controller_v39_dual_signal.py`: `be74c4e9fbf2aae4254bc94ff6bad9fda67270bf9656874a61f017d780d35a17`
- `research/doom/test_overlap_controller_v39_wait.py`: `10b6c377ab97d9d2ccae36d92f86acda61d5c6840286975caf80e3911fa377be`

Raw suite outputs and exit codes are in `results/`. `python audit_a02.py` independently verifies them and source identities. `SHA256SUMS` covers this README, audit program, audit report, and raw outputs. Construction evidence only.
