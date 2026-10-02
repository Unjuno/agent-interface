# Issue #6519 T0 — optional semantic-affordance regression envelope

Finite synthetic method study only. It tests whether a source-bound optional annotation gate preserves UNKNOWN, raw fallback, evidence provenance, and the separation between availability, semantics, goal appropriateness, authority, and task completion. The candidate receives only `fixture.json`; the independent `oracle.json` is mounted only for the auditor. It does not test a model, GUI, real application, or user benefit.

Run `python -B -m unittest -v test_protocol` for construction checks. The frozen formal candidate and independent auditor commands are recorded in `FREEZE.json` after preregistration. The candidate emits every frozen case/arm to raw JSON; the auditor reconstructs expected classifications directly from `fixture.json` without importing candidate code.

## Decision

`METHOD_PASS_SCOPED` requires every canonical arm to preserve source/focus/generation binding, keep raw evidence available, retain UNKNOWN for missing/stale/contradictory/unsupported cards, never grant action authority or completion from annotations, and keep effect claims explicitly unverified and separate from operational availability. An incorrect but source-matched card claim remains unverified and is reported as a disagreement, not an application effect. The five deliberately faulty arms must each trigger the independent auditor's corresponding invariant rejection. Any canonical violation is `FAIL_METHOD`; missing or malformed evidence is `STOP`.

No result transfers to annotation quality, fixed-model behavior, planner regression, task success, runtime safety, or a global gradual-typing guarantee. Those questions require a separate authorized T1.
