# First r03 targeted attempt

The first run of
`test_cancel_request_cancellation_does_not_drop_owned_operation` failed when
the injected `KeyboardInterrupt` escaped `complete_cancellation`. Inspection
showed the exception-clause edit had matched the earlier ordinary dispatch
handler, leaving the cancellation handler unchanged. That unrelated dispatch
edit was reverted; the cancellation worker now catches `BaseException` and
stores an UNKNOWN result. The targeted pair passed afterward, followed by the
full focused normal and optimized suites recorded in r03. The failed attempt
was a test-harness/code-wiring failure, not an X11 or release observation.
