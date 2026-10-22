# R02 raw and source audit — 2026-10-22 r01

This audit independently replays the frozen R02 report's hash and decision checks. It does not alter or replace the original run or raw files.

Run `python research/audits/standard_caller_xvfb_r02_raw_audit_20261022_r01/verify_r02.py` from the repository root. The script checks all 17 files in the R02 raw manifest, all five runtime source hashes against the current checkout, that R02's source commit is an ancestor of current `origin/main`, and that the relevant runtime directories have no diff since the run source. It reconstructs the timing and generation assertions directly from `raw/result.json`.

At current main `15030544befcb378d798da1c9c4ba847189d8f67`, all checks pass. Reconstructed times from cancellation admission are 252.924 ms to caller response, 324.791 ms to supervisor release readback, 331.456 ms to terminal cancellation receipt, and 379.339 ms to a separate parent X-client keymap readback. The late-request horizon observed all keys up and no delayed old `b` press at 8,501.475 ms after cancel start. A distinct target XID/session/process generation completed the synthetic task oracle from `[0]` to `[3]` at input and at horizon.

For the canceled old operation the runtime report remains `cleanup_status=UNKNOWN`, `late_server_request_possible=true`, `release_confirmed=false`, `task_success=null`, and replay denied. The new session's oracle passes synthetically while its runtime `task_success` remains null. This is one private-Xvfb schedule with the owner blocked in real `Display.sync()` while the X server remains responsive to the supervisor. It is not a whole-server-unavailable release proof, physical GUI/MAP01 result, reliability estimate, or matched-efficiency sample. No WSLc allocation was used.

`audit.json` is the machine-readable result. `SHA256SUMS.txt` binds this audit script, report, and README; the original run's own raw manifest remains authoritative for the frozen raw files.
