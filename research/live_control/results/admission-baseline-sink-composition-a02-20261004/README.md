# Admission baseline / accepted-event failure composition A02

## H / T / D / C / U

- **H:** The #7440-head ExecutorV12-derived admission-baseline candidate preserves the accepted-event delivery-uncertainty and shutdown behavior already present at #7429 head `7de3932c9435256796322b11409da1a6b09d6809`.
- **T:** Freeze the exact #7440 executor/import closure and baseline-hook candidate. Use one fake backend and a sink that records `accepted` then raises as if its acknowledgement were lost. Call `submit` once, inspect worker/backend/slot state, then call `close` once. No retries.
- **D:** The candidate composes safely only if input stays unstarted, uncertain admission remains explicitly fail-closed, and `close` does not fail joining an unstarted worker. A retained stale active/backend lease plus a join exception is `COMPOSITION_STOP`.
- **C:** The sink may have accepted the event before raising. Keep the command ID consumed and prevent input retry; do not infer that the receipt reached a real client.
- **U:** This uses exact executor source copies with a fake backend and sink. It does not test a transport, full session wrapper, game/scorer, X server, physical input, useful feedback, or recovery.

## Prior setup STOP

`PREVIOUS-STOP-A01/` preserves the first frozen attempt. Its runner failed at Python import with `ModuleNotFoundError: lease_cause_v1`, before the candidate module loaded or `submit` was called. That setup STOP was retained; A02 is a versioned successor with the missing exact #7440 dependency added, not a rerun of A01.

## A02 result

The frozen command ran once. The injected accepted-event sink raised after recording the event. The candidate did not start a worker or invoke the baseline callback, but kept the active slot and backend lease; `close()` raised `RuntimeError: cannot join thread before it is started`. No terminal or release event was emitted. The independent saved-record audit confirms source hashes and the lifecycle result. Classification: `COMPOSITION_STOP_REPRODUCED`.

The current #7429 source contains separate handling for accepted-event delivery uncertainty and an unstarted worker. This result shows that behavior is absent from the #7440-based baseline candidate. The session baseline hook is not ready for adoption until the two paths are composed and tested together.

## Reproduction

From this directory, verify `SHA256SUMS.txt`, run `py -3 -B run_candidate.py` only if conducting a separately authorized successor, then `py -3 -B audit_saved.py` to audit this saved result. The A02 candidate invocation has been consumed; do not rerun it.
