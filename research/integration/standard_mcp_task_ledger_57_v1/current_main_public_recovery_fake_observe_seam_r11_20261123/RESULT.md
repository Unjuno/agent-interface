# R11 result

**Disposition: `FAILED_TEST_ASSERTION_DESIGN` (not a product failure).** Both fresh invocations (normal and `-O`) exited 1 at the envelope-level `input_dispatched` assertion. The earlier assertions in the same test passed: the injected fake callback ran exactly once, its unique observation ID was returned in the raw observation report, and that raw report had `input_dispatched: false`. The outer MCP envelope carries a separate field and was not a valid oracle for the raw observation input flag.

No retry was made. R12 corrects only that test assertion and independently repeats the minimal fake injection check. R11 does not test task execution, recovery reliability, MAP01, efficiency, distribution, or native GUI behavior.
