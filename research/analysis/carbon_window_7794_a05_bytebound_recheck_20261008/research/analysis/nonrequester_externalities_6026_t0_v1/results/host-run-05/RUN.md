# Host T0 run 05 — method-scoped

- Candidate: `python3 -B candidate.py fixture.json`; exit 0. Captured stdout is `raw.json`.
- Independent auditor: `python3 -B audit.py fixture.json results/host-run-05/raw.json`; exit 0. Captured stdout is `audit.json`, status `PASS_METHOD_SCOPED`, 12 checks; it independently reconstructs from `fixture.json` and does not import the candidate.
- Construction CI: `python3 -B -m unittest -v test_method.py` — 9/9 PASS (including recipient omission, unsent-as-delivered, collapsed burst, double-counted review, and erased nonresponse controls).
- Syntax: `python3 -B -m py_compile candidate.py audit.py test_method.py` — PASS.
- Patch whitespace: `git diff --check` — PASS.
- Host runtime at capture: macOS `Darwin arm64`, Python 3.14.5; raw stdout timestamp 2026-10-01T12:51:20Z.
- Fixture inventory: 7 tasks × 2 routes; 27 event IDs with statuses `verified=14, delivered=10, performed=1, no_response=1, suppressed=1`.
- Stipulated route values: requester task-effect minutes plain=28, fast=14; collaborator active minutes plain=1, fast=17. Maximum within-burst event counts: collab-a=2 (4 active minutes), collab-b=3 (6 active minutes, including one six-minute cleanup event). The deferrable-alert burst itself is three events/three active minutes.
- Result: `PASS_METHOD_SCOPED` for synthetic ledger reconstruction only. No human attention, interruption, causal, joint-welfare, or product-effect claim.
- This is a host execution, not the requested OrbStack reproduction. The latter remains gated on explicit queue arbitration.
- Host-only run did not claim a formal frozen-main allocation. Current-main ancestry and all four source hashes must be frozen again at the authorized OrbStack start.

## Frozen source hashes at host-run-05

`fixture.json` `7f310012606f3d6085254ed43604dfbbde6033d08b921d9342c2a8d311dc003a`

`candidate.py` `b1f6c73c647b63d194d7fe28a3abb6c225598f4434f41db11973cfe98482ba56`

`audit.py` `8bd4b109d19f8d8ec27ee36351d020bf64e1da06ab1c41426d6c58968b1118b0`

`test_method.py` `977d540026291c85c081b59cf4e725e7c81a4db56a724a2d1346c64a674d2f91`
