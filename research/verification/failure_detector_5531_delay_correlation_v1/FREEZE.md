# Frozen execution record — Issue #5531 T4

Allocation: `fd5531-delay-correlation-20261001-01`
Branch: `research/5531-delay-correlation-v1-20261001`
Path: `research/verification/failure_detector_5531_delay_correlation_v1/`
Frozen main: `55c467786b3b98e5f8d1746f9c2970b7ada8b47c`
Preregs: `PLAN.md` Git blob `a43bb24c292f34b43517498a8cda4dafa08c88f1`
Construction record: `CONSTRUCTION.json` Git blob `d6a271e2583f008d1df01cb454baa64de52d9f44`

## Exact pre-formal source identities (Git blob SHA-1)

- Runner `experiment.py`: `2325536581d294f93e30213adfaa9b025721c52c`
- Tests `test_experiment.py`: `79fdd42e577e99cb4c956fefb0d1f7712a035c47`
- Independent raw-only auditor `audit.py`: `6896b86006540daf017361991de65929f81fe12f`

Construction was executed once on host CPython 3.11.9 / win32 by streaming these GitHub-readback sources in memory with `python -B`: 7 tests passed, 0 failed; auditor AST parse passed. No formal runner or auditor invocation has occurred.

## Frozen formal protocol

- Read these exact blobs back from the branch and verify the identities above before running.
- Invoke `experiment.main()` exactly once using host CPython 3.11.9, Python `-B`, in-memory GitHub-readback source; pass this FREEZE.md blob SHA as `FREEZE_BLOB_SHA`.
- Save stdout byte-for-byte as `FORMAL-01.json`; do not retry, tune, or replace.
- Only if runner exits 0, invoke exact frozen `audit.py` exactly once, with the exact raw result base64-encoded and this freeze blob SHA as its expected-freeze argument. Preserve audit stdout as `AUDIT-01.json`.
- Any command failure, mismatch, or failed gate remains STOP/FAIL evidence; no rerun under this allocation.

## Resource and scope disclosure

This is a local CPU-only synthetic simulator; the question does not require a language model or GPU. LM Studio was started only to verify local availability, then its model was unloaded and server stopped before construction; GPU was 9 MiB / 16 GiB used at freeze. No model inference or GPU computation is claimed. Current #5085 queue evidence assigns the only fresh container lease to #5156 Allocation 03, not this experiment, so Docker/OrbStack is deliberately not invoked. No network, GUI, OS input, real authority, or external action occurs in the simulation.

The formal result, regardless of PASS/FAIL, is conditional on the synthetic discrete-delay and witness-probability assumptions in `PLAN.md`. It is not a real failure-detector accuracy, safety, or liveness guarantee.
