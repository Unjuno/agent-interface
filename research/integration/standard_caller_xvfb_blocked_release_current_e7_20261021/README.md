# Current-main blocked-I/O release through the standard caller

This packet runs one version-pinned native-Wsl/Xvfb integration on current local main `e7d79d04de46202622873bf116adb909abb0dee2`. The public guarded MCP caller sends KeyPress(a); a real delayed XTEST request for key b is flushed on the same owner connection, then that owner blocks in the `python-xlib Display.sync()` response wait. The caller cancels and its separate XRes/release path is measured while the server remains responsive to independent connections.

## r01 result

The test and its copied independent auditor passed all 14 checks. The caller returned from cancellation in **770.070 ms**, within the 3,000 ms bound. XRes confirmed disconnection in **69.133 ms**; the separate release worker took **448.228 ms**. An independent X client read both keys up, and after **8,505.208 ms** the queued delayed `b` press had not appeared. The independent synthetic task oracle passed. The recorded owner-liveness sample preceded cancel return by **517.900 ms**; terminal result lookup took **9.075 ms**. Xvfb PID 673 was stopped after the run.

The caller conservatively retained `release_confirmed=false`, `cleanup_status=UNKNOWN`, `task_success=null`, and `replay_allowed=false`. That is an intentional distinction: the local Xvfb observer and task oracle confirm their scoped facts, while the public caller does not promote them to an end-to-end release or task-success claim.

The test also checks an independently read synthetic task effect, later keymap state after the 8-second delayed-request horizon, terminal caller uncertainty, and liveness-timestamp ordering. The frozen inputs and current runtime/test source hashes are in `CONDITIONS.json`; the exact pre-run hash verification is in `source-sha256.txt`.

The test's success criteria distinguish XTEST release/readback on a live private X server and the local task oracle from the public caller claim: the caller must retain `release_confirmed=false`, `cleanup_status=UNKNOWN`, `task_success=null`, and `replay_allowed=false`. This does not qualify a stopped X server, a physical desktop, WSLc, MAP01, a reliability population, or matched efficiency. No WSLc allocation, Docker, model, or external GUI was used. The single run must not be repeated under this run ID.
## Shared evidence copy

The local `raw/` tree retains the original unredacted records and is intentionally excluded from publication. `public-evidence/` contains text-only redacted copies, the publication redaction record, and a separate `SHA256SUMS`. Only local checkout/user-profile/cache paths and the local host name were replaced; measured values, statuses, timings, request records, and synthetic images are unchanged. Run the public-copy auditor from `public-evidence/` where provided.
