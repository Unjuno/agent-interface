# r03 — retain cancellation worker interruption as UNKNOWN

r03 follows r02 and adds one fault injection: the owner cancellation method
raises `KeyboardInterrupt` after the MCP request coroutine is cancelled. The
first attempt exposed that the cancellation worker's `BaseException` handler
had been applied to the ordinary action path instead of the cancellation path;
the exception escaped and the cancellation receipt could remain pending. That
first failure was corrected and its diagnostic is in `first_attempt_failure.md`.

After correction, the public MCP cancellation worker records an unknown
terminal operation, keeps `release_confirmed=false`, `task_success=null`, and
`replay_allowed=false`, and persists the same operation ID in
`cancellation.json`. Both focused suites passed 77/77 in normal Python and
77/77 under `-O`; raw stdout/stderr and exit codes are retained. The full source
is not separately re-pinned for this intermediate development run; r04 is the
canonical source-bound result. Its output-file manifest is `SHA256SUMS`.

This still has no prestarted cleanup process, whole-transaction deadline,
late-effect fencing, real-X11 release evidence, independent task effect,
recovery qualification, WSLc, MAP01, matched efficiency, or reliability result.
