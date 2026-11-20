# Pre-execution source/gate record

Issue: #5313
Allocation: BOUNDARY-BLAME-5313-T0-20261006-01
Base main: a3e6b0c1ab8d6af5c24abb88a451ce41c4ede028
Branch: research/boundary-blame-5313-t0-20261006

Construction: 4/4 unit tests passed after a construction-only ResourceWarning hygiene correction. No formal candidate/auditor/control invocation yet.

Complete frozen source capsule:
- SOURCE.tar.xz bytes: 5780
- SOURCE.tar.xz SHA-256: 641673195771c78a51c8767f35b900afe211541a7a6bfa9485c165b7870ffe53
- SOURCE.tar.xz.b64 bytes: 7810
- SOURCE.tar.xz.b64 SHA-256: 64428456df139202e45bb199b8f2513374d8d3d52642cf030248d7f461df9a2c
- FREEZE.json SHA-256: 3fb08918677dec8a4e90cadf9b5d3a15fced34ca2a79b58a6d08ea53af975c9e

Formal commands after remote byte readback:
1. python -S -B candidate.py --input public_cases.json --out formal/result.json
2. python -S -B audit.py --public public_cases.json --truth auditor_truth.json --result formal/result.json --out formal/audit.json
3. python -S -B controls.py --public public_cases.json --truth auditor_truth.json --result formal/result.json --out formal/controls.json

Candidate/auditor/control formal counts: 0/0/0. Retry budget: 0.
