# Public Win32 caller to actual backend — synthetic composition R01

Source: `de457b73e62dd1258be5590ab0f7aefd75b25b1d`. This is a test-only
composition through the existing injected producer factory. It does not add
a production native-input adapter or qualify Windows release behavior.

The public MCP bind/admit/start/cancel/results tools now have a single test
path through `OwnedWin32SessionOwner`, the prestarted cancellation supervisor,
a spawned `Win32RuntimeSession.dispatch()` / `Win32Backend.execute()` producer,
actual backend `release_all()` in a separate helper, and independent fake-state
readback. Only the external Win32 API is replaced by an inert fake. Target
generation and process-creation identity are explicitly synthetic.

| Injected schedule | Observed public result and event trace |
| --- | --- |
| DOWN blocked before fake acceptance | Recovered; exact producer exit precedes one recovery UP, then separate observer request. |
| DOWN accepted into fake state before its call returns | Same ordering; fake key state becomes neutral. |
| Accepted DOWN with producer refusing retirement | UNKNOWN; producer still live and fake key still down at assertion; no recovery or observer request, no UP, replay denied. |

Every schedule starts one producer despite a duplicate public start, reuses the
same cancellation ID for duplicate cancel, and creates no replacement helper.
The public action operation ID and generation match the actual child handoff
and recovery/observer requests. Release remains separate from task effect:
`task_success` and `task_effect` remain null. The existing public response
`input_dispatched=false` does not claim physical input from this fake path.

## Verification and sensitivity

- `raw-normal.txt`: 15/15 tests pass, exit 0.
- `raw-optimized.txt`: the same 15/15 pass under `python -O`, exit 0.
- These runs include three new joined-path tests, nine existing public-route
  tests, and three existing actual-backend/fake-API tests.
- `traces-normal/` and `traces-optimized/` preserve all six new-case event logs
  and public receipts before cleanup. The stubborn child is forcibly cleaned
  by the test afterward; its UNKNOWN receipt is not promoted to clean.
- `mutation_probe.py` injects a premature fake recovery UP before retirement.
  `raw-mutation.txt` records the expected assertion failure at the ordering
  check (`5 not less than 4`), one failure, exit 1. This is a negative control,
  not a regression in the unmodified runtime. It changes the test process only.

An initial development run had three harness errors: the test expected
`call_id` inside the producer action, whereas the contract stores it on the
outer caller record. The test was corrected to check that outer ID and its
action/cancellation operation links. That run's output was not captured to a
file and is not represented as a retained raw run or a runtime defect.

`conditions.json` lists exact commands and environment. `SOURCES.json` binds
canonical Git blob bytes at the source commit (not platform-dependent checkout
line endings). `SHA256SUMS` covers all packet files except itself; Git text
conversion is disabled for this packet. Earlier packets are unchanged.

## Remaining boundary

This closes the separate-test gap for this injected synthetic path. The public
route still requires explicit injected owner/producer factories, and this test
supplies the fixed program and fake API. It does not connect arbitrary caller
programs to a production native adapter. Native target identity, late queued
DOWN exclusion, physical neutralization, live task/MAP01 effect, hard latency
bounds, matched efficiency, and repeated reliability remain unqualified.
No WSLc allocation, Docker, or native desktop input was used.
