# T7 formal outcome — STOP

The single Dockerless WSLc auditor invocation exited 0 and emitted the expected 432-row, 432-case finite-oracle receipt. The preregistered host receipt verifier then exited 1 because it expected `failed_probe_yield_fallback_wrong_target`, while the unchanged auditor emits `failed_probe_yield_wrong_target` (value `0`). Since the frozen decision rule requires host verification to pass, this allocation is **STOP**, not PASS.

The source and raw SHA-256 values match before and after; the uniquely named `--rm` container is absent. No candidate ran, no retry occurred, and the frozen verifier was not replaced after observing the receipt. Keep the original #5309 STOP and T6 artifacts unchanged.

This demonstrates only that the exact bounded audit command ran in WSLc without Docker and produced a receipt. It does not establish Docker parity, speed or memory benefit, effective memory limits, OOM safety, or application/GUI behavior. Host memory snapshots are descriptive point observations only.

See `RUN.json`, `STOP.json`, `audit.stdout.json`, and the sanitized `host_verification.stderr.txt`; only the local absolute workspace prefix in the traceback is replaced with `<LOCAL_TASK_ROOT>` in the public copy. The frozen protocol and verifier are retained unchanged in the parent directory.

