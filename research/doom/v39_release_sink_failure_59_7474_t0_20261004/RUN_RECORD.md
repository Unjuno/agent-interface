# Exploratory construction run record

- Question: does #7474's exact V13 release publisher suppress a retry after sink failure without retaining delivery uncertainty?
- H: the pre-emit `published_release_ids` mutation causes both failure-before-accept and accept-then-raise sink outcomes to suppress a second attempt without recording an unknown-delivery event.
- T: AST-load only the exact `_release_event` and `_publish_cause_once` methods from #7474 head `3e498aebd77e500d5a7b1ac9d434d37350a9f597`; invoke each twice with a normal sink, a fail-before-accept sink, and an accept-then-raise sink.
- D: success control must publish once; sink-failure cases expose whether accepted state, retry behavior, and delivery-unknown custody agree with the observed sink outcome. Audit the exact `_run` call order separately.
- C: normal sink success.
- U: complete executor-thread integration, asynchronous watcher races, release/backend behavior, and real sink delivery are outside this probe.
- Run status: exploratory, not prospectively frozen; one invocation, no retry.
- Runtime: Windows CPython 3.12.10, host-only fake objects. WSLc inventory call remained live/unresponsive while many WSLc client processes were present; no container was launched.
- Command: `python research/doom/v39_release_sink_failure_59_7474_t0_20261004/run.py`
- Independent audit: `python research/doom/v39_release_sink_failure_59_7474_t0_20261004/audit.py`
- Outcome: all three fake cases classified as expected by the auditor. In both sink-error cases, the attempted release ID is marked published, retry is suppressed, and no `delivery_unknown` event is recorded. Static source structure shows the call precedes `release_all` and terminal publication inside `_run`'s `finally`.
- Comparison: PR #7429's current V13 source has separate attempted-ID and publication-error state with a wrapper that records release-event delivery uncertainty. Its exact-source tests already exercise a related sink failure. This run establishes that the tested #7474 source blob does not contain that equivalent guard; it does not independently validate #7429's full fix.
