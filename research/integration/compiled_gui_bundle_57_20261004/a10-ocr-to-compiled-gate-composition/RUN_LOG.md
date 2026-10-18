# A10 construction run log

The first run used the frozen construction code at commit `104d0664bc`. Its observer callback timestamped each synthetic observation 1 ms before capture. All 18 paths correctly refused with `SAFE_YIELD/stale_observation`; no Submit test-double action was dispatched. The run is retained as `RAW_ATTEMPT_01_STALE_OBSERVATION.json` (SHA-256 `6ad0dc403c4bf07b4b579a86a9a125c58b69389a0e442c26d889162cd63ba341`). The issue is in test-double observation timing, not in the OCR or formal A05 data.

The harness correction removes that artificial 1 ms offset. The plan, A09 OCR input, A07 adapter/core, expected task values, and exact-value decision rule are unchanged. The corrected candidate is separately committed before its construction rerun; the first output remains immutable.
