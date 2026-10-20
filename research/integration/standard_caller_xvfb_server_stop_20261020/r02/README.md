# Standard caller after private X server recovery — r02

This packet preserves the next distinct result after r01: cancellation remains UNKNOWN while the private X server is stopped, but an explicit `interface_close` after resume now makes one bounded release-only recovery attempt. The declared task still fails because the key is down at its deadline horizon.

## Source and run

- Change under test: PR [#9225](https://github.com/Unjuno/agent-interface/pull/9225), source head `52448ba887a12337690860751f4e900ee3a4a503`.
- Test source blob at that head: `runtime/cli_v1/test_mcp_xvfb_server_stop_integration.py`, `36575037dc255a52f00f3138534fcc252ceeacbb`.
- Workflow blob: `.github/workflows/runtime-x11-v1.yml`, `7a55cdd03b0a21f595860d8ba9166b4863008106`.
- Run: [GitHub Actions 39375915867](https://github.com/Unjuno/agent-interface/actions/runs/39375915867), job `x11-integration`, success. It used the workflow-owned Linux Xvfb `:88`; no WSLc, Docker, live provider, physical desktop, or MAP01 was involved.
- Raw report: [`RESULT.json`](RESULT.json), downloaded from artifact `standard-mcp-xvfb-server-stop` without editing. SHA-256: `3cb1bffc8b5c81471b5905205e9859fd862670695a039143b027e35c2aabdf85`.

## Conditions and observations

The standard owned caller held key `a` after the synthetic application committed effect `[1]`. The fixture stopped the exact workflow-owned Xvfb process with `SIGSTOP` while the owner was blocked in `Display.sync()`. The cancel response returned in 0.409653 s, before `SIGCONT` resumed the server and within the declared 3 s bound. The owner process exited with `-15`; disconnect observation timed out as `UNKNOWN` after 152.804 ms, so the cancel receipt correctly says `owner_release_attempt=not_attempted`, `release_confirmed=false`, cleanup `UNKNOWN`, `task_success=null`, and replay denied.

The separate parent X client still read `a` down both immediately after resume and at the 8.5 s horizon. The synthetic task oracle therefore returned `fail` / `task_success=false`, even though the application effect remained `[1]`. An explicit `interface_close` then returned in 0.646902 s. It rechecked XRes disconnect (`disconnected`, 73.769 ms), made a fresh release-only worker attempt (`readback_verified`, 568.630 ms), and a separate parent X client read both `a` and `b` up. This is a bounded post-resume cleanup observation in one synthetic Xvfb run; it does not turn the earlier cancellation into a confirmed release or make the expired-horizon task pass. The close receipt still conservatively reports `release_confirmed=false`, cleanup `UNKNOWN`, `task_success=null`, replay denied, and possible late server work.

The earlier `interface_results` record still contains `owner_process.alive=true` and `retired=false`, while later cancellation and close receipts show retirement. Source inspection shows `interface_results` rereads the original immutable `report.json`; it does not refresh the current owner snapshot. The records therefore represent different snapshots, not simultaneous liveness claims. The original report has no snapshot timestamp, so the exact sampling time cannot be reconstructed from this packet. Keep the distinction explicit; do not promote the old report to a live status reading.

## Interpretation and remaining boundary

The new explicit close path recovered key-up after the X server resumed without replaying task input or restarting the retired owner. The task deadline had already failed while the key remained held, and the earlier cancel result remains UNKNOWN. This is one scoped post-resume recovery sample, not a bounded release guarantee during a server-wide outage, a general X11 result, physical-input evidence, MAP01 task success, reliability estimate, or efficiency comparison. The fixture's later direct key release remains teardown only.

Keep Issue #17 open. The next discriminating work must preserve the outage-time UNKNOWN result, independently qualify the upper-bound across repeated blocked-I/O schedules, and then connect recovery to fresh observations and an independent application/task oracle. Do not rerun earlier allocations or claim a task pass from the post-horizon key-up.

## Integrity

`SHA256SUMS` covers the exact raw report and this README. The original Actions artifact remains the upstream copy.
