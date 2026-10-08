# Color ROI SNAP allocation01 — retained execution STOP

Disposition: `STOP_OUTER_EXECUTION_TIMEOUT`; scientific disposition is `null`. The frozen orchestration was invoked once and stopped after a 14/36 prefix. The retained `ALLOCATION_01_STOP.json` records 14 complete process receipts/rows and no terminal `RAW.json` or supervisor receipt. These rows are not pooled or promoted to PASS/FAIL.

The branch contains the exact eight additive files: frozen plan/environment/source and construction/audit checks, plus the STOP record. Its separate 9,200-byte partial archive is declared local-only (SHA256 `cf59dfe1469dd110a42fcdfb5dc36b4aa852737b31322482b1a0a13dcc4a7273`) and is not present in the branch; no additional raw rows are reconstructed here. No formal case is rerun in this rescue.

This path preserves only the source and bounded failure record, not a complete experiment result. Any successor must use a separately frozen execution envelope and retain the original STOP unchanged. Issue #4129 remains open.
