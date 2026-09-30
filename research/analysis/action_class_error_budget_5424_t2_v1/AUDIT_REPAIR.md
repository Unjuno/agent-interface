# Audit v1 correction record

The formal experiment was executed once and is not rerun for this correction.

The first raw-only auditor execution is retained unchanged as `raw/formal/audit.json` with status `FAIL_RAW_AUDIT`. It independently matched all 55,296 per-policy event rows to the 18,432 frozen input events and rejected all four mutation controls. Its summary-table cross-check failed on exactly three fields: `signal_missing_replicates` for the three stationary-policy groups. The stationary trace has no registered fault-onset/signal opportunity; the experiment correctly writes 24 missing signal replicates, while audit v1 left the count at zero because it skipped fault regimes without an onset. No decision row, outcome, raw input, or experiment result differed.

`audit_v2.py` preserves the v1 auditor and adds only the explicit no-fault signal-denominator correction to its summary recomputation. It writes a separate `raw/formal/audit_v2.json`; it does not overwrite `audit.json`, modify raw, tune the experiment, or rerun `experiment.py`. Both audit JSONs and their hashes are retained. The corrected audit remains a post-hoc repair to an auditor bookkeeping error, not a second formal experiment allocation.

