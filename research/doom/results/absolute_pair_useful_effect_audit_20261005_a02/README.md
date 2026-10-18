# Independent task-effect audit of retained coast/pulse windows

## H — Hypothesis
The six retained 600 ms coast/pulse windows contain enough independent scorer data to reconstruct whether either arm produced any positive task-progress signal, negative safety signal, or MAP01 exit before the frozen deadline. This audit reads only saved outputs; it does not rerun the consumed study.

## T — Treatment
An independently written raw-only parser checks each cell's result, raw event stream, scorer sample stream, scorer client-update stream, owner event record, final score, and saved source manifest. It joins scorer samples to producer updates by run id and sample sequence, and explicit key-up calls to their nested owner-thread receipts. It compares only observed MAP01 fields and uses `sample_ns` for the frozen window.

## D — Design
Six retained cells: three coast and three pulse. The window is `[window_start_ns, window_end_ns)` from each saved `RESULT.json`; the existing study specifies 600 ms. Raw inputs and this auditor are SHA-pinned before the one-shot audit. The auditor runs in the cached WSLc image with network disabled, read-only input source, and separate output mount.

## C — Criteria
The audit passes its evidence-integrity gate only if all six cells have valid 600 ms windows, all frozen input hashes match, result and runtime score agree, sample and producer-update identities join one-to-one, sample clocks are ordered, and the raw explicit-up receipts reconcile with per-key release rows. Task effect is classified only from independently sampled kill count, death count, player-dead, episode-finished, and map-exit fields. Missing health/ammo signals remain unobserved.

## U — Use and scope
A zero observed kill delta does not mean no visual feedback or prove absence of all possible useful behavior. These cells used no model and had no positive MAP01 progress or death; the scorer schema does not include health. This is a saved-data audit, not a new allocation or causal comparison, and it cannot establish bounded recovery efficacy or close #59.
This is audit attempt A02. A01's first outcome is preserved in the sibling package and failed only because it compared the complete `RESULT.json` score object with `runtime/score.json`; the latter omits the transport-only `emit_ns` field. A02 compares the five predeclared task/safety metrics field by field and otherwise uses the unchanged raw inputs, identities, time boundaries and key-up receipt checks. A01 is not overwritten or regraded.
