# STOP — formal runner schema mismatch

Allocation: `qwen05b-abstention-balance-4780-20260928-01`
Issue: #4988
Status: terminal STOP before any model fit; no scientific result.

The single formal Docker invocation exited with status 1 at `/src/run_formal.py:49` while checking the input digest. The runner indexes `freeze["formal_input_sha256"]`; the frozen schema places that field at `freeze["data"]["formal_input_sha256"]`. The runner therefore raised `KeyError` before model load/training/evaluation.

Formal seed fit invocations: 0. Retry count: 0. The frozen no-retry rule prohibits restarting this allocation. Host GPU remained 0 MiB / 0% at the post-run check. Existing containers were left untouched.

Raw terminal trace: `formal.stdout.log` (host-side local evidence; Docker wrote no output files).
