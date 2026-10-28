# Docker/Xvfb standard-caller blocked-release observations (2026-10-28)

These records are scoped to a synthetic X11 application on the Docker Desktop
Linux Engine. The container reports a Microsoft WSL2 kernel, but this is not
WSLc and says nothing about native Windows input or GZDoom MAP01. Raw attempt
packets are task-local under `private-packets/` and are not included in this
repository summary.

## R04 — prestarted cancellation supervisor

Current source: main `1988916cd0904b29e0a294dea24ec09ca0563ba3` (PR #9797).
Image: `sha256:bd191d30ea94871a1d3ca717252cd07a276e8ef7d1bcb4a130b63935ce075425`
(`linux/amd64`), network disabled, read-only container root filesystem,
private Xvfb `:88`. The integration test passed 1/1 in 9.495 s; Docker exited
0. Its structured report and observation image are retained in
`private-packets/docker_xvfb_standard_caller_prestarted_cancel_currentmain_20261028_r04/`.

The public standard caller reached the injected delayed `Display.sync`
response wait. Before cancellation, the synthetic application recorded one A
effect and an independent client read A down. Cancellation returned in
256.883 ms. The owned child exited with code -15 and XRes confirmed its client
disconnected. The prestarted supervisor's release attempt returned
`readback_verified`; a separate client observed A/B up. No delayed B press was
observed through 8,502.868 ms after cancellation began. A separate fresh
session dispatched its C task once; the independent counted-effect oracle
passed all nine checks, including exact effect count, neutral input at the
horizon, and preservation of the old call's fence. Final A/B/C readback was
neutral.

The old operation remains `cancel_unconfirmed`, `release_confirmed=false`,
`cleanup_status=UNKNOWN`, `task_success=null`, and `replay_allowed=false`.
The initial A effect preceded cancellation. The fresh C task result belongs to
a separate session and target generation. The independent neutral readback
and supervisor release receipt therefore do not certify the old operation.

## R03 — report-path defect

The same test body passed 1/1 and Docker exited 0, but the runner set
`AGENT_INTERFACE_MCP_XVFB_RESULT` while the test reads
`AGENT_INTERFACE_MCP_XVFB_BLOCKED_RELEASE_RESULT`. The structured report and
image were not retained. R03 is recorded as
`PASS_TEST_BODY_REPORT_MISSING`; its raw unittest log is not enough for an
audited release or task-effect result. It was not replayed.

## Direct XTEST follow-up R02

The lower-level current-main Xvfb test independently observed A down before
owner retirement, A remaining down after disconnect, a second client's
release transition to A up, no delayed B press through 8,500 ms, and final
neutral A/B state. The unittest passed 1/1, but a CRLF in the shell wrapper
made Docker's outer exit code 2. The inner test exit was 0; both are retained
in `private-packets/docker_xvfb_held_key_disconnect_currentmain_20261028_r02/`.
This direct XTEST result is not a standard MCP caller result.

## Limits and next discriminator

These are synthetic Linux/Xvfb samples. They do not establish a blocked X
server, native Win32 release, WSLc, real-app/MAP01 effect, MAP01 completion,
broad reliability, or matched efficiency. The next native discriminator
remains a fresh Win32 delayed-action/release trial with an exact task oracle,
same-generation neutral readback, bounded recovery, and retained raw evidence.
