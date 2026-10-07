# Result — admission-time scorer baseline barrier A01

The frozen fake-backend candidate exited 0 exactly once. Its saved-record audit passed with all three negative controls rejected. The experiment confirms the useful ordering seam and exposes a failure-path blocker:

- With the exact PR #7429 ExecutorV12 source, `submit()` synchronously invokes the `accepted` event emitter and only calls `worker.start()` after that callback returns. The synthetic baseline callback ran on the submit caller thread. The recorded order was internal accepted timestamp → accepted callback → synthetic baseline complete → `step_started` → first fake backend execution. While the callback was deliberately held open, the worker did not execute.
- When the synthetic baseline callback raised, no backend step ran, but `executor.active` remained set to `barrier-failure`, the one-shot ID remained consumed, and `backend.lease` remained set. The worker object was never started. The fake callback had observed the `accepted` object before raising; the harness does not prove whether a real transport would have published it. Source inspection shows the inherited `close()` joins the active worker, which was never started; that production cleanup path was not called here.

**Classification:** `BARRIER_CONFIRMED_FAILURE_PATH_STOP`. A scorer baseline can be placed after internal admission and before input, but the callback cannot be installed as an ordinary fallible emitter hook. Executor submission needs an explicit baseline-gate outcome and cleanup/terminal behavior before this seam can qualify a real recovery interval.

This was host Python 3.14.5 on macOS with a fake backend and a synthetic `{tick: 41}` callback payload. It did not run the MAP01 scorer, ViZDoom, X11, a model, a live executor, physical input, or the dedicated recovery allocation. It provides no task-effect, latency, or live-recovery evidence. The earlier OrbStack daemon content-store preflight failure was not retried; see `FREEZE.json` for this construction-only runtime deviation.

Reproduction from this directory:

1. Verify the frozen inputs: `shasum -a 256 -c SHA256SUMS.txt`.
2. The one-shot candidate has already been consumed; do not run it again.
3. Recheck retained output integrity: `shasum -a 256 -c ARTIFACT_SHA256SUMS.txt`.
4. The saved-only audit result is in `AUDIT.json`; its single run is captured in `AUDIT.stdout.txt` and `AUDIT.exit.txt`.
