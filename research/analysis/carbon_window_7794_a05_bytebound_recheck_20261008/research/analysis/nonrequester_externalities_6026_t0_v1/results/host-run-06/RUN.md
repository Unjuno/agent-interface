# Host T0 run 06 — current method result

- Base main at execution: `6d34916b31e4a7b26cda339a7ea7439ddb8dfdd4`. This is a host method run, not the later OrbStack allocation freeze.
- Candidate: `python3 -B candidate.py fixture.json`; exit 0. Exact stdout is `raw.json`.
- Independent auditor: `python3 -B audit.py fixture.json results/host-run-06/raw.json`; exit 0. Exact stdout is `audit.json`; result `PASS_METHOD_SCOPED`, 54 dynamically counted assertions across named categories.
- Host CI: `python3 -B -m unittest -v test_method.py` — 11/11 PASS, including candidate and independent-auditor duplicate-assignment controls.
- Syntax: `python3 -B -m py_compile candidate.py audit.py test_method.py` — PASS. Patch whitespace `git diff --check` — PASS.
- Host: macOS `Darwin arm64`, Python 3.14.5; candidate stdout timestamp 2026-10-01T13:07:01Z.
- Inventory: 7 offered tasks × 2 routes; 27 event IDs; statuses verified=14, delivered=10, performed=1, no_response=1, suppressed=1.
- Stipulated outcomes: requester task-effect minutes plain=28, fast=14; collaborator active minutes plain=1, fast=17. Maximum burst rows: collab-a count=2/minutes=4; collab-b count=3/minutes=6. The three deferrable alerts specifically form a 3-event/3-minute burst; the 6-minute max is the separate cleanup event.
- Result: method-scoped ledger reconstruction only. No human attention cost, interruption effect, causal, joint-welfare, or product claim.
- OrbStack reproduction: not yet run; follow `CONTAINER_PROTOCOL.md` only inside the owner-bound #5085 window after exact start-gate revalidation.

## Frozen source SHA-256 at host-run-06

- `fixture.json`: `7f310012606f3d6085254ed43604dfbbde6033d08b921d9342c2a8d311dc003a`
- `candidate.py`: `336f82b82d920a70c7272db8064d2b4a94babbd2fda9780daabddc5be52fdb33`
- `audit.py`: `c9435a477805e445c14dc1dce090c9991425dfd3378e6f29c8077c00d2a93ce0`
- `test_method.py`: `a29f9319893a72b2a84c6846ccb2d97a562ebdd9acb168e3806ef95746b4c7c2`
