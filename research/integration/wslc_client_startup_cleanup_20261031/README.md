# Integrated Chromium client: failed startup cleanup

The earlier current-main WSLc attempt (PR #9977) failed because Chromium was unavailable, but the caller exposed a bare `StopIteration` when no `ready` event arrived. Because `__enter__` had not completed, its `__exit__` cleanup was not called. The client now reports a specific missing-ready error, attempts to terminate and wait for its owned child on any startup failure, closes the error stream and cleans its temporary journal directory. It preserves the original error if cleanup itself fails, attaching a diagnostic note; a failed process wait is still an unconfirmed cleanup, not proof that the child died.

Three local regression cases reproduce missing ready, request failure and cleanup failure; together with the related model/caller suites, 18 tests passed in network-isolated Linux Docker. Two separately fixed no-model WSLc runs then used the candidate with a private Chromium/Xvfb environment:

- e04 deliberately specified a nonexistent executable. The client reported the explicit missing-ready error; the real owned child had exited, the error stream was closed, the temporary directory was gone, and retained stderr contained the missing-executable diagnostic.
- e05 used `/usr/bin/chromium` and reached the actual `ready` event, then closed normally. Both named containers were absent afterward.

These are startup checks, not task-effect, real-time or MAP01 evidence. No model call was made. `public.zip` retains frozen conditions, runner, candidate source/test, subprocess logs, receipts, source-hash and cleanup summaries. `python audit.py` checks hashes, the two expected outcomes and the candidate's two changed files against the preceding main-source packet. Full source and image bytes are omitted. Historical OCR experiment records remain unchanged; their separate command-metadata discrepancy is documented in PR #9984. Issue 57 remains open.
