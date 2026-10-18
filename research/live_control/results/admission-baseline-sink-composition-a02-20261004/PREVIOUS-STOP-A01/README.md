# Admission baseline / accepted-event failure composition A01

## H / T / D / C / U

- **H:** The #7440-head ExecutorV12-derived admission-baseline candidate preserves the accepted-event delivery-uncertainty and shutdown behavior already present at #7429 head `7de3932c9435256796322b11409da1a6b09d6809`.
- **T:** Freeze exact #7440 executor/import sources and the baseline-hook candidate. Use one fresh fake backend and an event sink that records `accepted` then raises as if its acknowledgement were lost. Call `submit` once, inspect worker/backend/slot state, then call `close` once. No retry.
- **D:** PASS only if input remains unstarted, the uncertain admission is explicitly preserved, no stale state causes close to fail, and no release is claimed. A stale active/backend lease plus an unstarted-worker join exception is `COMPOSITION_STOP`.
- **C:** The sink may have accepted the event before raising. The conservative action is to keep the command ID consumed and prevent any input retry; do not infer that the receipt reached a real client.
- **U:** The emitter, backend, and lease are local fakes around exact executor source files. This does not test a transport, session wrapper, game/scorer, X server, physical input, useful feedback, or recovery.

## Result

The one-shot probe is frozen in `PRE-RUN.json`; its complete state snapshot is `RAW.json`. The independent auditor checks source hashes and recomputes the expected lifecycle observations. The tested baseline candidate emitted an `accepted` event and then received an injected acknowledgement exception. It did not start a worker or call the baseline callback, but left the active slot and backend lease set; `close()` raised `RuntimeError: cannot join thread before it is started`. The candidate reported no terminal or release event. This reproduces the missing accepted-sink failure handling on the #7440-based candidate; it does not contradict the separate handling present in #7429's source.

The main practical consequence is that the baseline hook is not ready to compose into the session path until the accepted-publication uncertainty and unstarted-worker shutdown semantics are brought forward and tested on the same candidate.

## Reproduction

From this directory, run `py -3 -B run_candidate.py` once, then `py -3 -B audit_saved.py`. The candidate was executed once after `PRE-RUN.json` was written; do not rerun it. `SHA256SUMS.txt` covers all retained files except itself.
