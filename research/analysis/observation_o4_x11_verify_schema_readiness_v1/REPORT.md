# O4 retained live-X11 schema-readiness audit

Decision: **HOLD_O4_X11_SCHEMA_INSUFFICIENT**

This is a posthoc transfer audit of the retained main result `research/container_control/live_two_dispatch_x11_v1/result.json` (blob `8d7690c3d215aa7f0dae5a4b394a2b6042b67456`) against the exact #1650 gate (formal.py blob `606f167803058d1e4a8aa65ff6e72ffae804a8d8`). The old X11 allocation was not replayed.

## Frozen observations

The retained result has six arms: FRESH 3/3 with positive exact effect deltas and `verified_effect`; STALE 3/3 with `SAFE_STOP/stale` and no second right keydown. Its retained per-arm keys include condition, outcomes, call order, effect values, release state, and pass/fail. It does not retain current `obs`, current `intent`, `verdict`, `input_authority`, or `semantic_authority`.

The naive predicate (`FRESH + verified_effect + exact_effect_delta > 0.015`) would suppress escalation for 3/3 FRESH rows and 0/3 STALE rows.

## Strict projection

Projecting only retained fields into #1650 leaves every arm without the required current lineage and tri-state verdict. No row is locally admitted; all six strict decisions are UNKNOWN/escalate. No lineage, authority=false, or verdict was inferred from filenames, condition labels, source constants, or posthoc scorer knowledge.

Directed controls reject fabricated obs, fabricated intent, inferred authority=false, and stale relabeled as verified. Candidate/oracle agreement is exact for the frozen projection.

## Scope

This is schema readiness only. It does not re-prove live X11 efficacy, measure latency, model-call/token savings, or promote runtime behavior. A future successor must add per-result current obs/intent/verdict and explicit authority flags to fresh/private-X11 evidence; it must not replay this allocation.
