# Outer execution-surface note

After the frozen candidate, auditor and control commands each returned exit 0 and all formal evidence files had been written, the enclosing execution surface reported status 1 and printed `TERM environment variable not set.`.

The scientific commands were not rerun. Their individual exit receipts and exact stdout/stderr hashes are retained in `formal/EXECUTION_END.json`. This note records the outer wrapper anomaly separately; it is not a scientific PASS/FAIL signal.
