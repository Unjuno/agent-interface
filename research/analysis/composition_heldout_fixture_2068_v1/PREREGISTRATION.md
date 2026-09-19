# Issue #2068 — held-out composition fixture v1 preregistration

Status: FROZEN PREREGISTRATION / NO RESULT

This additive fixture is the smallest next rung for the end-to-end composition issue. It does not claim model, GUI, latency, or task efficacy.

## H/T/D/C/U

- H: A composed path that carries current provenance, bounded local continuation, and typed effect evidence can preserve correctness at a model boundary where a compact cue changes the next decision.
- T: Compare BASELINE_FULL_MODEL_PATH, COMPOSED_INTERFACE_PATH, and COMPOSED_PATH_FALLBACKS_DISABLED over frozen held-out traces. The composed path must expose cue use, effect outcome, UNKNOWN, raw fallback, retries, preflight, and skipped stages.
- D: A deterministic standard-library harness with source observations, action receipts, target/session/epoch identity, bounded continuation budget, typed effect outcomes, and an independent oracle. Primary metrics are task correctness, effect correctness, stale/unsafe action count, cue-to-next-decision influence, and complete accounting of model/retry/preflight/fallback stages.
- C: Composition boundary errors, stale or missing provenance, UNKNOWN collapsed to success, cue present but unused, fallback loss, or accounting that omits failed/skipped calls.
- U: Live model behavior, real GUI effect verification, real token/latency benefit, and transfer to DOOM or production remain unverified.

## Frozen controls

1. correct effect with cue used;
2. cue present but ignored by next decision;
3. stale target during model wait;
4. missing provenance;
5. UNKNOWN effect;
6. effect success but task failure;
7. model-call failure and retry;
8. raw-detail fallback;
9. fallbacks disabled;
10. lease/expiry or local-continuation cancellation.

## Stop rules

Stop and retain the first outcome if the independent oracle cannot distinguish task correctness from effect correctness, if any stale/unsafe action is emitted in a control, if raw evidence or critical events are unavailable, or if accounting omits a failed/retried/skipped stage. No retry or tuning after the first formal invocation.

## Integration boundary

Owned path: `research/analysis/composition_heldout_fixture_2068_v1/**`. No shared runtime/workflow edits. Formal execution and report require a later PR after source freeze and independent audit.
