# Raw auditor receipts — T6

Raw input for all observations: SHA-256 `39adda08f06e1a15b3e74ac05660c49d2112e806635db63cbe90d9fea65208b2`.

1. Preregistered audit invocation: `python audit_raw.py`; exit 0; output `{"errors": [], "result": "PASS_AUDIT_V1_SCOPED", "rows": 4}`.
2. During later final-verification tests, `test_accepts_exact_four_row_replay` loaded this same raw and called the audit function; it passed. This post-formal validation was not part of the preregistered single audit.
3. The same final-verification command also accidentally invoked `python audit_raw.py` again; exit 0; same output, same unchanged raw. This violated the one-audit limit.

The first observation is not erased. Later checks are not relabeled as a new allocation or independent replications. Preserve all three; do not rerun the candidate or auditor. T6 terminal disposition: `STOP_PROTOCOL_DEVIATION`; no formal PASS is claimed.
