# Win32 in-flight recovery fence — R01

This packet records a synthetic concurrency check for `Win32RuntimeSession`.
The question was whether a direct session could emit recovery UP while a
synchronous `SendInput` producer was still unresolved, or admit a second
producer on the same session.

The test runs the production `Win32RuntimeSession.dispatch()` and
`Win32Backend.execute()` methods against an inert fake API. It freezes two
schedules: the fake accepts DOWN and then blocks before returning, and it
blocks before accepting DOWN. In both schedules, concurrent `recover_input()`
and a second dispatch must return `pending` with
`INPUT_PRODUCER_UNRESOLVED`; neither may emit UP, a second DOWN, or replay.
After the test releases the fake barrier, the original producer completes its
terminal release and state query. The fake key state is neutral, exactly one
UP was sent, and the deferred recovery flag clears.

The retained normal and optimized logs each report 76 tests passing. The suite
also includes the existing supervised-session, backend integration, and MCP
session tests. The original run, one intermediate rerun, and the final rerun
are preserved separately. Exact environment and SHA-256 values are recorded
beside this report.

This is a Python-thread/fake-API result. The barrier has a test timeout; it does
not impose a native API deadline or terminate a blocked Windows call. No native
input, WSLc, container, or Docker operation occurred. It does not establish
physical release, bounded recovery, task effect, MAP01, efficiency, or
reliability.
