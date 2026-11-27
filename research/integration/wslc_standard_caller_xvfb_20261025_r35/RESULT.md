# R35 — pre-Xvfb stop: temporary filesystem was noexec

**Disposition: STOP_PREINPUT, no Xvfb or test input.** The pinned container initialized the staged runtime, but Python execution failed with `Permission denied` before the test runner began. Inspection of the exact stopped container confirmed that `/tmp` used a tmpfs without the `exec` option. The staged interpreter is copied into `/tmp/stage`, so it must be executable there.

R35 made no caller request and emitted no input. Its exact container was removed and verified absent. R36 adds `exec` to that private tmpfs while retaining the 2 GiB/2 CPU limit, network isolation, and read-only host mounts. R35 is not retried.
