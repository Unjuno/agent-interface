# Standard-caller prestarted cancellation + fresh-session recovery R03

**Run ID:** `AI-XVFB-PRESTARTED-FRESH-RECOVERY-20261022-R03`
**Purpose:** one independent repeat of R02 under identical conditions against the current-main source.
**No WSLc or Docker allocation is used.** This uses the local Ubuntu WSL2 distribution and a private Xvfb socket hidden by a per-run mount namespace.

## Question

Does the public MCP standard caller again return within the independently defined 300 ms target while its owner is blocked in real `Display.sync()`, then release/read back held input and allow a distinct fresh target/session/process generation to pass the synthetic task oracle, while preserving the old cancellation as UNKNOWN and replay-denied through an 8 s delayed-request horizon?

## Frozen method

Run exactly once against current-main SHA `6b276fcabfa11c060282e0714501a1057e75c0a6`, invoking `runtime.cli_v1.test_mcp_xvfb_blocked_release_integration.StandardCallerBlockedReleaseXvfbTests.test_standard_caller_cancels_blocked_sync_and_releases_on_xvfb`. Use the existing R02 local pinned dependency cache only if it is already present and versions match `python-xlib==0.33`, `Pillow==10.2.0`, `numpy==1.26.4`, `mcp==1.30.0`; do not install or download dependencies for this run. Use Ubuntu 24.04 WSL2, CPython 3.12.3, Xvfb 2:21.1.12-1ubuntu1.8, display `:88`, TCP disabled, one-second withheld owner acknowledgement, and an eight-second delayed keypress. Run in an unprivileged user/mount namespace and overlay a temporary mode-1777 tmpfs on `/tmp/.X11-unix` inside that namespace only. Preserve exact invocation, conditions, dependencies, Xvfb identity/log/PID, stdout/stderr, exit codes, result JSON and SHA-256 hashes under `raw/`.

The unittest's 3000 ms assertion is not the research criterion. Evaluate caller response independently against 300 ms. Require exact distinct XID/session/process-generation, all-up independent readback at release and at the horizon, fresh task oracle success at input and horizon, no delayed old press, and unchanged old UNKNOWN/replay-denied fence. This is one replicate, not a reliability estimate.

## Stop conditions

If the distro identity, dependency versions, private socket overlay, private Xvfb readiness, source SHA, or raw destination cannot be verified before unittest invocation, preserve the preflight as HOLD and do not invoke the candidate. Do not retry R03 after the candidate test starts. Never inspect or mutate WSLc/Docker/container/image state for this run.

## Known limitations

One Xvfb schedule cannot establish reliability. This does not show release while the entire X server is unavailable, physical GUI/MAP01 success, owner-exclusive control of global XTest state, matched efficiency, or Windows/WSLc portability. Runtime task-success for the canceled operation must remain null and replay denied.
