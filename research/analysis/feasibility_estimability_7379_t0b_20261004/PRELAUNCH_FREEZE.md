# Prelaunch freeze

Allocation `ESTIMABILITY-FEASIBILITY-7379-T0-20261004-02` for Issue #7379. Frozen `origin/main`: `13bab54ea6d91978247ecc1b70e5060db752367a`. This is a new allocation after `...-01` stopped before candidate invocation when main advanced; its preserved STOP is in the separate `_t0_20261004/` path.

- Spec SHA-256: `b58d3158607070f59c9f0ad7a1399c8d254f4930cb22ff94438270e19a995129`
- Candidate SHA-256: `d203298cb732bec12d1c162c878840a35293387014db736e323295f2c68c01bc`
- Independent auditor SHA-256: `0b901fa72d0553ce93f6cd3652b01491671d3edc4a6884cee7ae2d25cb54fbd1`
- README SHA-256: `f1ebf7f1d71050b3f3298c4333fb046595d55054e82c9a22756ca1ad97467e3c`
- Runtime: Python 3.14.5 standard library; macOS-27.0.1-arm64-arm-64bit-Mach-O; 10 CPUs visible.
- Candidate invocation budget: 1; auditor: 1; retries: 0.
- Candidate command: `python3 candidate.py spec.json output/raw.json freeze.json`
- Auditor command: `python3 audit.py spec.json output/raw.json freeze.json`
- Fresh empty output path: `output/`; first outputs are immutable.

Preflight passed: live remote main equals HEAD; #7379 is open/unassigned with no comments; bounded PR search found no matching PR; no remote #7379 branch exists; source compiles; six construction smoke checks pass; output path is empty. The T0 is standard-library exact finite computation only, with no model, GUI, GPU, container, or external outcomes.
