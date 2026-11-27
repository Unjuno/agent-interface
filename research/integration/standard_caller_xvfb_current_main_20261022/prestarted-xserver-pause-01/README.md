# Private-Xvfb server-pause boundary R01

**Run ID:** `AI-XVFB-SERVER-PAUSE-BOUNDARY-20261022-R01`
**Baseline:** main `b3fdbee40cce6e9040c9a3a9360ea35cc692995e`
**Candidate test harness:** `a85868f5deb36616db972b83edb591593db6986f`
**Environment:** Ubuntu 24.04 WSL2; private unprivileged mount namespace and Xvfb `:88`. No WSLc or Docker allocation.

## Result

The standard-caller integration test passed once (unittest 1/1; test exit 0), and Xvfb exited 0. The test verified the exact private `/usr/bin/Xvfb :88` process entered `SIGSTOP` and an independent timer resumed it after 1,500.674 ms. The cancellation request was admitted 54.687 ms after the harness started the tool call. From server admission, the public response returned pending in **253.566 ms**, inside the fixed 300 ms response budget, while Xvfb was still stopped for another 1,193 ms. The whole in-process harness interval from before the tool invocation to response was 308.253 ms; this includes pre-admission dispatch and is reported separately rather than substituted for the server's admission-based deadline.

The public response kept `cleanup_status=UNKNOWN`, `release_confirmed=false`, `task_success=null`, and replay denied. After Xvfb resumed, the supervisor's release readback completed in 59.355 ms and a separate parent X client observed all keys up in 98.039 ms. The delayed-request horizon at 8.505 s found all keys up and no old delayed press. A distinct fresh target/session/process generation passed the synthetic `[0] -> [3]` task oracle. The old cancellation remained UNKNOWN and replay-denied throughout.

This is scoped evidence that the standard caller can return within its admission deadline while the entire Xvfb process is stopped, and that cleanup proceeds promptly after that server resumes. It does **not** show input can be released while X11 itself is unavailable. The test does not establish physical desktop/MAP01 behavior, XTest owner exclusivity, reliability, matched efficiency, or WSLc portability. The runtime deliberately does not promote the canceled task to success.

## Integrity and execution notes

`PLAN.md` and `conditions.json` froze the 1,500 ms pause, pinned existing dependency cache, 300 ms admission-based response target, one-second owner acknowledgement withholding, eight-second delayed request, and one-shot/no-retry rule. `raw/` retains the command, private socket proof, source identities and hashes, dependency/preflight records, test stdout/stderr/result JSON/screenshot, Xvfb log/PID/exit, and post-run process check. Both raw and packet-level SHA-256 manifests are included.

The initial Windows execution-tool call returned at its 10 s streaming boundary without exposing the outer shell's final status. The candidate's unittest and Xvfb exit codes are directly recorded as zero; the test outcome is preserved. No retry was made to recover a wrapper receipt.
