# Result S05

**HOLD — WSLc API initialization failed before session creation.** This is a retained preflight failure, not a Fake X execution result.

The single `dotnet run --no-build --no-restore` invocation exited `-532462766` (`0xE0434352`). Its stderr records `System.TypeInitializationException` from the generated module initializer, caused by `System.DllNotFoundException` for `wslcsdk.dll` or a dependency with Win32 error 206 (`ERROR_FILENAME_EXCED_RANGE`). `api.stdout.jsonl` is empty, so no `GetMissingComponents` result or WSLc version was emitted by the API harness. The process stopped before `Session.Start`; no image pull, container creation or container ID occurred. The exact S05 storage path remains absent. S05 was not retried.

Preflight facts remain useful: current main and the pinned source baseline both equal `2166707229958e095d472c80e160c26449de7a29`; the prepared image is digest-pinned; dependencies and 247 runtime/probe files are frozen; the WSLc CLI reports 3.0.3.0; the API harness compiled with zero warnings/errors. The built `wslcsdk.dll` was copied under an application output path of 252 characters (including the DLL name), making path-length-dependent native resolution a concrete candidate explanation, not a proven root cause.

The S05 probe/audit did not run. No Fake X case, release, environment response, cancellation, recovery, task effect, or computer-control outcome is inferred. The overall classification stays HOLD even if a later attempt works. `api.stderr.txt`, empty `api.stdout.jsonl`, this post-hoc exit receipt and the S05 conditions are retained as-is; there was no global WSLc inventory or Docker command.

A fresh S06 may be considered only as a distinct attempt with new unique session/storage/container names and a short native-harness output path. S06 must retain its own source freeze and raw result; it cannot replace S05.
