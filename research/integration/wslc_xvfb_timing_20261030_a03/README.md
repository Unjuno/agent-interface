# WSLc Xvfb cancellation observation timing A03

One predeclared exploratory successor to A02, using WSLc 3.0.3.0 and an isolated Xvfb synthetic app. Conditions, exact command, image identity and test-file SHA256 were recorded before execution. The source starts at main 459b0c92dc66d9d99d2a887c653d244892cd7242 with the companion test instrumentation changed.

All five tests passed. The receipt records the terminal cancellation result followed by a locked process-state observation of the same Xvfb incarnation in state T; its monotonic process-read interval lies between the recorded stop and resume. The lock excludes the test's own safety-timer resume during that read; this is test-produced evidence and does not exclude an external actor. Old cleanup remains UNKNOWN with no replay; the newer client's A hold survived old close, a fresh target on the same X server produced a passing independent synthetic-task oracle, final A/B were up, and the exact-ID cleanup query was empty. Nine checks were recalculated from the receipt and cleanup result.

This does not retroactively add timing to A02, establish display-generation isolation, prove old task success, establish general reliability, complete MAP01 or compare performance.
