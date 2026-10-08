# Construction experiment freeze

H: On this Windows 11 host's Ubuntu WSL Python 3.12.3, the current-main `CodexAppServerClient.close(timeout)` may time out on its reader after terminating only its direct app-server child when an owned descendant inherits stdout/stderr. A narrowly scoped alternative that launches the direct process in a new session and sends termination to its process group may retire the reader and descendants within the same timeout.

T: Two fresh one-parent/one-grandchild processes run the exact current-main client source from main `4d42238694c55aaa29bf47cb13a5b8d4c5d4074a` (path `research/live_control/codex_app_server_client_v2.py`, Git blob `85f7f5129920e2fb3bceeefaabf99cc1cf1483b3` as reported by file API; local SHA-256 frozen separately). Arm A uses unmodified Popen session and exact `close(timeout=0.20)`. Arm B uses `start_new_session=True` and substitutes only the child process's termination primitive with `killpg(SIGTERM)`, then calls the same exact `close(timeout=0.20)`. Each child launches one 30-second grandchild inheriting the real app-server stdout/stderr pipes. Record process/pgid state and reader completion; explicitly clean up only the test's own residual PIDs. Python standard library only; no network, GPU, provider, model, GUI, or app-server actor.

D: PASS for the scoped mechanism if A reports reader-close TimeoutError while the grandchild is still alive, followed by cleanup, and B returns from exact close without timeout with the grandchild terminated and reader joined. FAIL if candidate B leaves its grandchild/reader; HOLD for fixture, host, or audit errors. This does not qualify production close, cross-platform behavior, task effect, or physical input release.

C: A process group can kill unrelated processes unless the child is isolated in its own new session; an already-exited direct child creates a race unless ProcessLookupError is handled. WSL's init may delay reaping orphaned grandchildren. This one observation is a mechanism check, not reliability/frequency evidence.

U: WSL Ubuntu (Python3.12.3), not WSLc/container; `wslc.exe` is unavailable and Docker Desktop's configured engine is offline. Two local synthetic arms only. Source owner retains the repository file; no product source or branch edit is planned.

