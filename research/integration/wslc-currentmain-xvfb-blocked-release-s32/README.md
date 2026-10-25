# S32 current-main WSLc private-Xvfb replicate

S32 is one new, preregistered, uniquely named WSLc SDK session for the same 3,935 ms current-main private-Xvfb standard-caller task as S29. S30 and S31 are retained setup HOLDs: the API-created sessions were terminated, but `wslc.exe --session <name>` returned `ERROR_PATH_NOT_FOUND` before any image/container/task input. Microsoft documents the cross-session CLI lookup, so this local failure is still unexplained.

S32 avoids that cross-process lookup. It relies on a new SDK `Session` object with a GUID-suffixed name and absent storage path, then creates and manages its one GUID-suffixed container directly through that session handle. It does not enumerate existing sessions or containers. All source and runtime assets remain read-only except the empty output directory.

The one formal invocation started and terminated the uniquely named SDK session. `PullImageAsync` was invoked, but the SDK threw `System.IO.DirectoryNotFoundException` synchronously before any pull progress, completion, container creation, or task input. The exception record contains HRESULT `0x80070003` and two localized path-not-found messages, but this harness did not record a stack trace or identify the missing path. The image was not confirmed pulled; cleanup receipt says `pulled=false`, `cid=null`, and the session terminated. Independent audit is in `AUDIT.json`; raw files are mirrored under `raw/` with source hashes. Classification: `HOLD_PRETRIAL_SDK_SESSION_PATH_FAILURE`, no retry of S32.

This narrows the failure from an unready cross-process CLI lookup to the direct SDK pull invocation on a freshly started session. It does not identify which directory is missing or establish that WSLc failed to create a session. A future attempt needs explicit `pull_started`/`pull_returned` markers and `Exception.ToString()` before using another fresh allocation; do not use this evidence to justify retrying S32.

The trial is synthetic private-Xvfb evidence only; it cannot establish physical Windows input, MAP01 or live application control, reliability, a stable threshold, provider/model economics or clearance of unrelated shared WSLc ownership.
