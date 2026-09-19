# Temporal-ring history for model-facing GUI disambiguation (#2045)

## Result

**PASS_CONTROLLED_TEMPORAL_EVIDENCE_FIXTURE_SCOPED**

A frozen ten-case GUI-like evidence fixture was executed once in `python:3.12-slim` (Docker 29.4.0). The four arms share the same evidence schema:

- CURRENT_ONLY
- JIT_EQUIVALENT_HISTORY
- CONTINUOUS_RING_HISTORY
- CONTINUOUS_RING_WRONG_WINDOW

The deterministic oracle passed. The ring resolved the ambiguous-current/predecessor case to `SAVED`; current-only returned `UNKNOWN`. Wrong-window, dropped-interval, other-surface, historical-as-current, and unavailable-interval controls returned `UNKNOWN`. Stable current evidence, stale identity, irrelevant history, and no-visual-effect controls retained their expected outcomes.

Digest: `4d5a6d38982484c8f34e24c7693318731112ce9e046cdc9f5d532cdec9a97532`.

Counters: model=0, X11=0, task-input=0. Formal container run=1; reruns/tuning=0.

## Boundary

This is a controlled evidence/oracle fixture, not a live X11 capture and not a multimodal-model evaluation. It establishes schema, provenance/scope filtering, explicit UNKNOWN behavior, and a task-relevant predecessor witness only. It does not establish model correctness, latency, input cost, attention utility, or end-to-end agent benefit. The next rung must reuse this frozen case ledger with an actual controlled X11 source and fixed model-facing comparison.
