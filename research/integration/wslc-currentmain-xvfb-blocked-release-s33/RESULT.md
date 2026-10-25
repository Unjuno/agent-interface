# S33 current-main WSLc private-Xvfb result

**Decision: `PASS_SCOPED` (21/21 independent checks).** One newly named WSLc 3.0.3 SDK session ran the current-main standard-caller private-Xvfb blocked-release case with the pinned S29 assets and 3,935 ms pause. The session was created with a fresh, absent storage path. The SDK pull returned normally, the pinned image was pulled, one container ran the test, and SDK cleanup deleted the exact container and image and terminated the exact session. The runner and container both exited zero.

The owner release receipt was independently verified all-up 3,953.343 ms after cancellation admission, within the 4,000 ms transaction bound. A separate parent X client read all-up at 4,023.879 ms, within the 5,000 ms readback bound. At 8,503.074 ms the delayed-request horizon remained all-up and observed no delayed `b` keypress. Both the old-task and fresh-session task oracles passed with exact synthetic effect counts.

The old public cancellation intentionally remains `pending`/UNKNOWN with `release_confirmed=false`, `replay_allowed=false`, and runtime `task_success=null`; its completed release receipt does not rewrite that public state. The separate synthetic task oracles report scoped success. Fresh-session close used fail-closed cleanup after owner retirement.

S33 adds evidence about the earlier S32 `DirectoryNotFoundException`: with markers around the `PullImageAsync` call and full exception-chain logging, S33's SDK call returned and the pinned pull completed. Thus the S32 path failure is not reproduced as a stable SDK/session-path failure; its cause remains unknown. S30/S31's exact-name CLI lookup errors also remain preserved as pretrial HOLDs. S33 does not establish physical Windows input, live-app/MAP01 control, efficiency, a timing guarantee, or reliability.

## Evidence and custody

- Preregistration and frozen source/input hashes: `PREREGISTRATION.json`, `SOURCE-FREEZE.json`, `CONDITIONS.json`.
- Full independent audit and measured bounds: `AUDIT.json`.
- Raw harness and container outputs: `raw/`; original file hashes and lengths: `raw/RAW-SOURCE-SHA256.json`. Readable mirrors mask the local account name; original raw files remain under `%LOCALAPPDATA%\agent-interface-research\wslc-s33-b87c4e2f9a16`.
- Exact SDK cleanup receipt reports `started=true`, `terminated=true`, `pulled=true`, `imageDeleted=true`, `deleted=true`, container exit zero, and no failure.
- After session termination, its unique 234,881,024-byte `storage.vhdx` remains retained at the session's own storage path. SHA-256: `6bf2ee4c9efc1976d274722b0eb6111f97870f08bb269b366def315a30affd51`. It has not been deleted or inspected as a shared allocation.
- No Docker operation or global WSLc inventory was used. No WSLc process remained after the run.
