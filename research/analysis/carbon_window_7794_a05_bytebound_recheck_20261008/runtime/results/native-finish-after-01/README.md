# Native finish-after: one explicit terminal action response

The existing research exchange supports finish-after behavior, but the native
Calc/Inkscape harness required a separate finish request after every last action.
It now accepts a strict boolean `decision.finish_after=true` on a normal action.
After ordinary dispatch, release, feedback and window review, it evaluates the
saved artifacts and cleans up before publishing one immutable terminal reply.
That reply contains the action, last reviewed observation, evaluation and cleanup.
No next-stage source is published. The default and separate finish remain.

**This is an explicit request to close the private allocation.** It does not
mean that the task succeeded. Even if scoring fails, the session ends; use it
only when no further interaction is intended. A dialog or uncertain intermediate
state should normally use the existing boundary response for another decision.
Non-boolean finish_after and simultaneous finish=true/finish_after=true are
rejected before input. No repair, input replay or automatic confirmation occurs.

The returned image is the last reviewed capture **before evaluation and cleanup**,
not a new screenshot of an already closed application. Its original sequence,
timestamp, path and hash remain. A client timeout resumes the same request
read-only; it must not resubmit the action.

The pre-frozen primary-assistant Inkscape seed 991105 run viewed the initial image,
selected edge (600,378), waited50ms, repeated Right18, waited50ms and saved with
finish_after=true. One response supplied the x=86 image, independent task success
and completed cleanup. The owner handle73470 exited0. This has exactly the same
26 expanded operations/43 emissions as `native-key-repeat-01`, but **one request
instead of two**. Local exchange elapsed approximately906ms; this excludes model
deliberation and host tool overhead and is not a matched latency improvement.

Two retained negative controls:
- Fresh invalid string `finish_after="true"`: needs_review, no action/program,
  preserved x=50, cleanup completed, owner25736 exited1.
- A separately predeclared task-negative clicked and saved without movement:
  finished session, evaluation.success=false, last image x=50, neutral release,
  cleanup completed, owner58797 exited0. No correction was attempted. Its roughly
  3.80s exchange includes the existing failed-score wait; false is not promoted.

Disposition: **PASS_NATIVE_FINISH_AFTER_SCOPED**. Existing exchange/review/cleanup
tests pass28. The independent archive audit verifies source freeze, one request
per new allocation, unchanged successful operation list, image links, saved SVG,
separate task/cleanup results, and rejects corrupt request and image digests.
The task-negative plan was added before that allocation, without changing the
original two-case plan or source. This does not establish generalized app behavior,
human-tempo, model cost/token benefit or causal speedup. No sensors/helper models
were developed or used; Docker was not restarted.

Run `python3 runtime/results/native-finish-after-01/audit.py`. Exact base and live
source hashes are in SOURCE_FREEZE.json; snapshots and raw artifacts are retained.
