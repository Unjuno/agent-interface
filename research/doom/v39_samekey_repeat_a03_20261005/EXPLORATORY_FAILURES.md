# Preserved STOPs and auditor correction

- A01 stopped before either sequence began because the isolated checkout omitted the current-main `bridge.py` imported by the current-main test harness. The two STOP records are copied byte-for-byte to `results/previous_a01_STOP_RAW.json`.
- A02 reached one fake F8 key-down per case, then stopped because the manually constructed release backend lacked its `emit` callback. Its partial traces are copied byte-for-byte to `results/previous_a02_STOP_RAW.json`.
- A03's first independent auditor source was too strict about release-batch grouping and assumed a scenario label absent from emitted rows. Its full FAIL_AUDIT output and code remain as `results/AUDIT_V1_FAIL.json` and `audit_v1_failed.py`. The corrected auditor checks the preregistered identity/timing gate and passes. The candidate was not rerun.
