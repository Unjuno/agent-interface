# Win32 supervisor custody packet — 2026-10-23 R01

This packet preserves the local synthetic result for the approved prestarted Win32 supervisor implementation plan. It is source-bound to the commit in `conditions.json`.

The production `OperationCancellationSupervisor` starts exactly one recovery helper and one observer helper before the public operation can be started. Each must send the exact ready receipt, remain alive, and match its retained PID/creation-time identity. Cancellation reuses those processes over request/result/completion exchanges. Missing, malformed, late, or mismatched receipts remain `UNKNOWN`; invalid helpers are not replaced.

`test_supervised_session.py` runs the actual `Win32RuntimeSession.dispatch()` and `Win32Backend.execute()` paths with an inert fake `user32`, shared fake key state, and a parent-traced process handle. It covers a DOWN blocked before acceptance, a DOWN accepted into fake state before the call blocks, and a producer retirement timeout. In both successful schedules, the log records confirmed producer exit before the fake backend recovery UP, then a separate neutral-state observation. The timeout schedule stays `UNKNOWN` and emits no recovery UP.

The public caller accounting regression verifies one producer start and one oracle reservation per attempt. A timed-out Generation-A oracle later returns a fabricated success receipt, but the retained result remains byte-for-byte unchanged UNKNOWN with no receipt, no task success and replay disabled. A fresh Generation-B attempt receives its own producer and oracle call and scores separately.

## Verification

The normal and optimized runs each passed 79 tests: 22 pure backend/session tests selected from `test_integration.py` plus 57 fake custody, backend ledger, process identity, owner and public caller tests. The existing MCP owned-process and guarded-X11 identity compatibility suites passed 67/67 in normal and optimized mode. Exact stdout, commands, and exit codes are preserved in the four `raw-*.txt` files. `SHA256SUMS` covers the packet files other than itself; `SOURCE_SHA256SUMS.txt` binds relevant source, test, and design files.

The native `Win32IntegrationTests` class is intentionally excluded from both valid runs. During an earlier broad command it was accidentally included. It started the repository fixture GUI and failed at `self.assertGreater(self.backend.emissions, before)` with `0 not greater than 0`. The test output did not establish whether an unsuccessful native API call or any other fixture-side effect occurred. A process query afterward found no `fixture_app` process. The incident is preserved separately in `incident-invalid-native-test.md` and is not qualification evidence. Do not rerun that class.

## Limits

This packet has no physical Windows input/release evidence and does not qualify native `SendInput`, late-DOWN exclusion, a live application or MAP01 task oracle, global input exclusivity, hard real-time bounds, matched efficiency, or repeated reliability. It uses no WSLc allocation or Docker. The implementation remains synthetic-only and opt-in until separate native gates pass.
