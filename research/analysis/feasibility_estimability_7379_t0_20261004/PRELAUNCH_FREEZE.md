# Prelaunch freeze

Allocation: `ESTIMABILITY-FEASIBILITY-7379-T0-20261004-01`. Issue #7379. Frozen main: `f11ee9d051239094cf3679e19c80bd7deaed0564`.

- Spec SHA-256: `b58d3158607070f59c9f0ad7a1399c8d254f4930cb22ff94438270e19a995129`
- Candidate SHA-256: `e5acc43f2349708ae5f9ee2625b14335f0dcd0b0b6b5a87207707f2c4ce4ce8b`
- Independent auditor SHA-256: `0b901fa72d0553ce93f6cd3652b01491671d3edc4a6884cee7ae2d25cb54fbd1`
- README SHA-256: `42e80c53a0c07be5cceba2ada06f0e45ba29cf41ff877515245cbe81e9e6220e`
- Runtime: Python 3.14.5 standard library on macOS-27.0.1-arm64-arm-64bit-Mach-O; 10 logical CPUs visible.
- Invocation budget: candidate 1, auditor 1, retry 0.
- Candidate: `python3 candidate.py spec.json output/raw.json freeze.json`
- Auditor: `python3 audit.py spec.json output/raw.json freeze.json`
- Output: fresh `output/`; first outcomes are immutable.

Preflight: latest remote main was checked immediately before this freeze; Issue #7379 remains open/unassigned; no matching PR or branch existed; both sources compiled; six construction smoke checks passed; no model, GUI, GPU, container, or external outcome data are used.
