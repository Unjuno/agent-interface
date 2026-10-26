# R11b result — independent recovery-to-task replication

**Classification:** `PASS_RECOVERY_FRESH_GENERATION_TASK`  
**Source:** `cca812f7a9305e9a5c0f843618e4cff44708749a` (merged main)  
**Host/runtime:** user-authorized Windows PC; Python 3.13.14  
**Primary audit:** 18/18 checks; six pretrial and 50 raw hashes pass.  
**Corrected additive audit:** 11/11 checks; the same pretrial/raw hashes pass.

The held-SHIFT recovery gate completed in **16.862 ms** against its 3 s deadline. Retained custody reported release confirmed, and a native same-generation readback observed SHIFT up. The first fixture exited cleanly before a second fixture with a new PID and target generation was created. A stale-generation public dispatch was refused with `TARGET_GENERATION_CHANGED`, `input_dispatched=false`, and no effect file.

One low-effort `gpt-6.1-sol` App Server decision consumed the fresh fixture observation, selected `(120,90)`, and reported 10,263 input, 19 output, and 0 reasoning tokens (8,192 cached input tokens). The repaired runner comparison matches every reported usage field present in the retained App Server journal. One standard compiled caller action then clicked the selected point, typed `office`, and saved only in the fixture. Its release receipt, independent native all-up readback, fresh post-dispatch observation, exact fixture event/effect, and independent task oracle bound to the exact action call, operation, oracle ID, and generation all passed. The fixture and App Server exited cleanly; foreground was restored.

The frozen copied `audit_followup.py` remains as a failed supplemental artifact because it hard-coded R11's old oracle ID. It did not alter or supersede the passing primary `audit.json`; `audit_followup_corrected.py` reads the preregistered R11b oracle ID and independently passes. The failed first supplemental output is preserved unchanged.

Scope remains limited to an owned Win32 fixture. The block is injected before native `SendInput`, so this is not an OS/kernel hang guarantee. This replication does not establish MAP01, WSLc, production-app control, or a reliability rate. No WSLc or Docker resource was used. Raw files and SHA-256 manifests are retained under `run/` and in each fixture/session folder.
