# Execution status: held before candidate invocation

The formal test in `PLAN.md` has not run. The only Xvfb launch attempt failed at server socket setup before the unittest process started. Its Xvfb log and attempted PID are preserved under `raw/preflight-*`; no candidate stdout, stderr, result JSON, or candidate exit-code file exists.

The captured environment is Ubuntu 24.04.3 WSL2, CPython 3.12.3, Xvfb `2:21.1.12-1ubuntu1.8`. The shared `/tmp/.X11-unix` is root-owned, mode 0777, and read-only. Xvfb requires mode 1777 and cannot create its UNIX listener; root chmod was rejected by the mount. No Xvfb process remained and display `:88` was free.

A separate setup probe confirmed that an unprivileged user/mount namespace can mount a private tmpfs at `/tmp/.X11-unix` with mode 1777. This does not alter the shared WSLg socket directory and provides a safe basis for a separately recorded run. Preserve this packet as the original preflight hold; the candidate run, if executed, belongs in the distinct `prestarted-fresh-recovery-02` packet and must use its own frozen conditions.

No WSLc or Docker instance/allocation was used. The separate [local Fake X packet](../../local_fakex_standard_session_recovery_20261022_r01/README.md) is synthetic regression evidence and does not substitute for real X-server ordering.

The separate R02 candidate trial has since run under a private user/mount namespace and is documented at [R02](../prestarted-fresh-recovery-02/README.md). R01 remains an unexecuted candidate and preflight-only history.
