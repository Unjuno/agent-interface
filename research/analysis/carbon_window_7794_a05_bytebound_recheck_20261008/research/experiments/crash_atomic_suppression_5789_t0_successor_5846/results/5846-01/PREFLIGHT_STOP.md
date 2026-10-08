# Allocation `crash-atomic-suppression-5846-t0-20261001-01` — terminal preflight STOP

Disposition: `STOP_MAIN_ADVANCED_AT_FORMAL_START_GATE`. This is a resource/provenance STOP only, not a scientific result. The allocation is consumed; do not retry it or create its guest after the failed gate.

- Reserved window: 2026-10-01 07:35–08:05 UTC.
- Frozen preparation base in `FREEZE.md`: `56ef267db50a8937f04d940a425b2b1819f714fb`.
- Frozen source commit in `FREEZE.json`: `e96d9aabd4f64547f4f67a50b27596d9523b6fa5`.
- Immediate 07:34:43 UTC GitHub `refs/heads/main` read: `fc1f06474149d81989099e5220c7aa197c142c6a`.
- 07:35:16 UTC start-gate `git fetch origin main`: still `fc1f06474149d81989099e5220c7aa197c142c6a`, unequal to frozen base.
- OrbStack running-guest inventory at 07:35:16 UTC: empty.
- Candidate=0; auditor=0; Docker containers=0; successor guest created=0; retry=0.
- Candidate/audit output directories under `results/5846-01/` were absent at the gate. No source, output, or predecessor record was changed by a formal invocation because none occurred.

The queue reservation explicitly requires STOP before candidate on any main drift. No guest was created, no shared daemon was accessed, and no candidate/auditor was invoked. A later attempt requires a distinct fresh allocation and a new immediate start gate; this consumed allocation is never reused.
