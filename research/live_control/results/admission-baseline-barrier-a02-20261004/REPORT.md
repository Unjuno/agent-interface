# Result — admission-baseline callback failure repair A02

The frozen candidate ran once and exited 0. The corrected saved-record auditor passed and rejected all three negative controls. For both ExecutorV12 and ExecutorV13 at PR #7429 head `e22e59732033438916415f71b53f86695b1c448a`:

- The injected accepted-callback/baseline failure was recorded as `admission_publication_errors[id] = {status: delivery_unknown, error: {type: RuntimeError}}`.
- No backend step ran; the worker remained unstarted. The active slot, one-shot ID, and backend lease remained retained, preventing further admission under an uncertain accepted-event outcome.
- `close()` returned without the unstarted-thread join exception. The active slot remained retained on the closed executor. ExecutorV13 also removed its unstarted release watcher registration.

**Classification:** `FAIL_CLOSED_SHUTDOWN_CONFIRMED`. This validates the accepted-sink failure and shutdown repair for these V12/V13 fake-backend paths. It does not prove the real scorer hook or transport behavior, nor does it address the separate V13 release-sink failure path identified in review on #7429.

The first auditor v1 failed on an incorrect expectation that the error object include a message. Its raw result is retained unchanged. Corrected audit v2 matches the frozen producer contract and passes; see `AUDIT_DISPOSITION.md`.

Host Python 3.14.5 on macOS; fake backends only. No VizDoom, game, X11, model, live input, task effect, or recovery allocation was used. The sample payload is not a game observation.

The exact source snapshots retain their upstream trailing blank line; the package-scoped `.gitattributes` suppresses only trailing-whitespace diagnostics for those frozen snapshot files so `git diff --check` can still validate the new evidence package without rewriting source bytes.
