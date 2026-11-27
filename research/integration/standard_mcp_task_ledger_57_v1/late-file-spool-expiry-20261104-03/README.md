# Late file-spool completion after caller deadline (2026-11-04)

## Question

Does a valid App Server completion receipt published after the one-second
planner deadline reach the public MCP caller if it lands before the outer
provider wrapper returns?

## Frozen synthetic setup

One Fake X Calc task first performs a registered compiled change and verifies
its independent fixture state effect and input release. A second model attempt
uses the actual `FileSpoolPlanner` shared-directory protocol. Its synthetic
host worker publishes `started`, waits until the planner observes its deadline,
then writes a complete protocol journal and immutable `completed` receipt with
a valid action payload. The recorder/public caller is invoked once; no retry is
permitted. The test requires the late receipt to arrive before the outer caller
returns, then checks that no new public tool call is submitted and the task
state remains byte-identical to the already verified state.

Four identical-condition executions passed: Windows Python 3.11 normal and
optimized (`-O`), and pinned networkless Docker Python 3.11 normal and `-O`.
The configured planner timeout was 1.0 s. Observed outer-call durations were
1023.980, 1024.330, 1322.650 and 1332.170 ms; late-receipt publication followed
the deadline by 2.430, 2.320, 38.500 and 38.410 ms, respectively. In every run
the late completion arrived before the outer wrapper returned; public tool call
submission remained false, release checks remained true, and the before/after
application-state SHA-256 matched. These are four fixture runs, not a statistical
reliability estimate or comparison against another route.

## Scope and limits

This is synthetic Fake X + synthetic host-worker evidence. It demonstrates the
timeout/late-receipt disposition through the local public-MCP composition
boundary for this test fixture. It does not establish live provider behavior,
physical desktop input release, Calc GUI behavior, model token economics,
latency advantage, MAP01, WSLc, broad recovery, or Docker long-duration
stability. All four timed-out attempts retain 55 input and 9 output tokens as partial usage from the late journal; no count is inferred as zero or treated as complete usage. No production runtime code
was changed; the additive regression test fails if late output is dispatched.

## Files

- `conditions.json`: host, image digest, timeout and comparison boundary.
- `commands.txt`: exact Windows and Docker commands.
- `*-run-01/output.txt`: exact test stdout/stderr.
- `*-run-01/fake-x/.../run/`: full raw provider ledger, protocol journal,
  spool request/inflight/start/completion receipts, Fake X traces, independent
  state/effect artifacts and measured timing JSON. Each raw run has its own
  SHA-256 manifest. `SHA256SUMS.txt` covers every packet file except itself.
- Source test SHA-256: `09bf1f33b808123cc04f75ae987f4cca96f47091ac6f8633bc811b5503fd326d`.
