# Deadline clock call-path check DCLK-R01 (2026-11-13)

## Question and decision

Does the current merged Win32 MCP clock-only path report one high-resolution monotonic domain in the parent, a real spawned child, and the stdio MCP server before any target or input is opened?

**Result: PASS for this clock-only preflight.** Parent, spawned child, and server ran CPython 3.14.2 and reported `QueryPerformanceCounter()`, monotonic, non-adjustable, 100 ns resolution. Two `interface_clock` replies passed the retained same-host bracket check and carried the same `server_instance_id`. The child exited successfully. The packet records no target startup, backend opening, authority, lease, or dispatched input.

This is a finite clock qualification only. It provides no input-release latency, deadline guarantee, task effect, GUI response, recovery, or reliability evidence.

## Reproduction and evidence

- Attempt: `DCLK-R01-20261113`
- Source: current merged main `d11ed28bc6c815f008f56911cd880be38bcd50f8`
- Runtime: `private-runtimes/map01-qpc314/Scripts/python.exe`, CPython 3.14.2, Windows AMD64
- Probe: `research/integration/map01_numeric_ammo_oracle_20261111/clock_preflight_probe.py`
- Acceptance helper: `research/integration/map01_numeric_ammo_oracle_20261111/execution_clock_preflight.py`
- Conditions and raw outputs: `private-packets/deadline_clock_currentmain_callpath_20261113_r01/`
- The packet's four-file SHA-256 manifest was recomputed; every listed file's hash and byte count matched.

## Relation to earlier deadline evidence

- D05 isolated Windows Python 3.11 `monotonic_ns()` as `GetTickCount64()` with 15.625 ms resolution. Rechecking that coarse deadline after a high-resolution wait did not materially improve the 2 ms poll. A one-shot timer without rechecking is only a lower bound and is unsafe as a lease implementation.
- D06's no-input QPC loop (200 randomized waits) measured p50/p95/max overshoot of 0.275/0.547/0.694 ms with 2 ms polling. This excludes process retirement, recovery IPC, Win32 UP, and readback.
- R142's 10 ms-poll native run exceeded its fixed 20 ms outer release bracket: 41.941 ms. Its conditions did not pin the actual clock implementation and did not timestamp exact `SendInput` entry/return, so the cause is not isolated.
- R145 measured a 7.5713 ms phase-only journal write before cancellation began, 4.6279 ms producer retirement, 2.1481 ms recovery backend creation, and W-UP API return 16.0664–16.4276 ms after expiry. R146 moved cancellation ahead of that write and passed at a 12.0067 ms outer bracket; the W-UP call overlapped the write. These are single instrumented runs, not a general bound.
- R157 passed one actual MAP01 task/effect/release path using the same QPC preflight, but did not exercise exception-only reconciliation. It also does not establish reliability or matched efficiency.

Together, these observations support using an explicit same-host QPC precondition for the qualified caller path. They do not establish that `time.monotonic_ns()` is high-resolution on every supported Windows Python. The separate Python 3.11-to-3.14 custody experiment below verifies that this v1 journal persists no absolute monotonic timestamp and preserves UNKNOWN across the clock change; it does not qualify every recovery deadline or caller path.

## Local regression coverage

`test_execution_clock_preflight.py` adds eight focused acceptance/rejection cases for same-host QPC metadata, bracket containment, server-instance continuity, and the clock-only/no-authority response. Run against the pinned Python 3.14.2 runtime in normal and optimized mode; both runs passed 8/8. These tests validate the caller precondition, not runtime lease behavior.

## Persisted custody across clock implementations

A second isolated experiment used actual separate interpreters and a unique temporary journal, outside the current user's custody store:

- Python 3.11.9 wrote `status=unresolved`, `phase=unknown`, and `input_dispatched=true`. Its monotonic clock was `GetTickCount64()` at 15.625 ms resolution.
- After the writer exited, Python 3.14.2/QPC reopened the same journal. `require_recovery_source` returned the exact persisted obligation, and a fresh admission was rejected with `ORPHAN_RECOVERY_UNRESOLVED`.
- The journal stayed byte-for-byte unchanged (506 bytes; SHA-256 `f2091d4b1b6a7e2d923a8a2b852a2af8fa273ab9e93fc1ba450b89950b59d272`). Neither `monotonic_ns` nor `deadline_ns` appears in the stored state.
- Conditions, both executable scripts, stdout, and the isolated journal are retained under `private-packets/deadline_clock_custody_cross_runtime_20261113_x01/`; the manifest covers all packet files.

This directly qualifies storage and fail-closed admission across these two Python clock implementations. It does not test production `for_current_logon` storage, recovery scheduling after restart, physical release, or whether any separate recovery deadline is initialized correctly. It supersedes the concern that this v1 custody journal might reinterpret a persisted absolute monotonic timestamp: the journal does not persist one.

## Next discriminating step

Exercise the exception-only reconciliation branch in the production supervisor on an isolated target, with custody remaining unresolved until release/readback evidence is durable. Capture recovery deadline creation, helper request/return, exact Win32 UP entry/return, independent readback, and custody resolution using one qualified QPC domain. Then run a fresh MAP01 attempt only if that local branch qualifies. Keep raw conditions, process identity, clock metadata, exact call entry/return, and independent task oracle in each packet.
