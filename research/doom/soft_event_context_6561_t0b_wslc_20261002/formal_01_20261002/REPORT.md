# Issue #6561 T0b — scoped method result

Allocation: `SOFT-EVENT-CONTEXT-6561-T0B-WSLC-20261002-01`
Branch: `research/soft-event-context-6561-t0b-wslc-20261002`
Frozen base: `926144e0bbbc197e00aa3b4821f1d49afe831529`
Runtime: native Microsoft WSL Containers (`wslc.exe`) 3.0.1.0; cached Python 3.12.14 image `python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`.

## Result

**`PASS_METHOD_SCOPED`.** Construction, candidate, and independent auditor each ran exactly once in separate WSLc containers; all exited 0. Construction passed 8 test groups. Candidate emitted the six frozen baseline cases. The independent auditor reconstructed all six with zero errors. Candidate raw and auditor input copies match byte-for-byte (SHA-256 `fc148f5e6586c00ac5f53773770b78637e7c87cbb628b6d3b8d398d44ce04bda`). The auditor reports 0 external effects and 0 model calls.

The tested boundary includes source/event rebinding, six contradictory guard flags, missing or relabeled expiry receipt, float/bool/negative sequence values, future event, changed event count, and prompt authority/success injection. The exact frozen controls and decision rule are in `PREREGISTRATION.md`; machine-readable outcome is `audit_output/audit.json`.

## Runtime record

Commands, timestamps, image, WSLc version, and exits are preserved in each stage's `RUN.json`, with stdout/stderr and `exit.txt`. All three stages emitted: `wsl: Your kernel does not support swap limit capabilities or the cgroup is not mounted. Memory limited without swap.` Thus a 512 MB memory limit was requested, but swap limiting was unavailable; no stronger host enforcement claim is made. The run used one CPU, no network, no image pull, no GPU, and non-root UID 65534. The auditor received the raw candidate file through a read-only mount after a verified byte-identical copy.

## Scope boundary

This is a finite synthetic serializer/auditor method result. It does not execute the production controller, game, model, GUI, or input; it does not establish observation truth, planner use or benefit, production safety, or any MAP01 task outcome. It does not resolve the live-control gate in Issue #59. Prior #6568 host-only construction and the separate T1 adversarial result remain unchanged; this is a fresh additive successor.

## Retained files

- `../README.md`, `../cases.json`, `../candidate.py`, `../auditor.py`, `../test_protocol.py`
- `PREREGISTRATION.md`, `FREEZE.json`, `runner.ps1`
- `construction/`, `candidate_output/`, `audit_input/`, `audit_output/`
