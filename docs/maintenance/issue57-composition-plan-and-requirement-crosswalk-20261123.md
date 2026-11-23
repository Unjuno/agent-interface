# Issue #57 composition plan and requirement crosswalk

**Audit base:** current main c4065d011e1297ebd589bcd5b85da3beb269e037.
**Purpose:** decide the smallest coherent current bundle and record which existing evidence supports it before a live matched allocation.

## Selected composition

1. **Acquisition and accounting:** research/live_control/adaptive_acquisition_caller_v3.py owns cold/warm route decisions, every model attempt, usage, image count, wait, timing phase, typed stop, repair, execution outcome, and outer effect receipt.
2. **Grounding provider boundary:** V3PersistentGroundingAdapter over PersistentGroundingModel/CodexAppServerClient supplies current App Server identities, per-turn usage and terminal status. R03-R07 tests verify synthetic JSONL results through durable custody; they do not qualify an external provider.
3. **Compiled local continuation:** runtime/core_v1/compiled_gui.py is called only from the caller execute adapter. Its symbols are target references, not coordinates or authority. Each transition observes fresh state, chooses one branch, re-admits the target, executes, verifies terminal/release, and observes the expected effect. The second action must depend on that intermediate observation.
4. **Schema and authority:** schema_preflight_gate_v1.require_compatible remains before GUI authority; the runtime's existing target admission/input owner remains responsible for scope, freshness, expiry, cancellation and release.
5. **Task result:** compiled program completion is not task success. The caller's separate verify_effect adapter must retrieve retained evidence and independently score the final effect.

Exclude another compression mechanism, local model, Rust rewrite and optional asynchronous-provider path. They are not required to test this bundle.

## Requirement-to-evidence matrix

| Requirement | Current enforcement/test evidence | Current status and gap |
|---|---|---|
| #52 typed stop: no match, ambiguity, unavailable evidence | Caller v3 _decision/STOP_REASONS; test_unconfigured_failure_stops_without_model_or_input; compiled runtime typed SAFE_YIELD and unknown/ambiguous tests | Offline contract covered; no broad live distribution estimate |
| #53 complete accounting, including failed attempts and missing usage | Caller v3 model()/finish(); test_cold_anchor_path_preserves_full_accounting, test_failed_model_attempt_retains_available_accounting, test_capacity_deferral_is_not_generic_failure; durable App Server R03-R07 | R01 now composes full cold caller accounting with the compiled local continuation in a synthetic fixture. Live current-provider all-attempt joins remain unproved |
| #54 compatible schema preflight before authority | schema_preflight_gate_v1.require_compatible, preflight gate tests and archived compiled GUI live V5 cache-hit record | V5 records the boundary for caller v2; no current-v3 full comparison with cold preflight costs |
| #55 revalidate after model wait and before input | Caller v3 final_revalidate; test_post_model_changed_evidence_stops_before_input, test_stale_same_frame_receipt_fails_closed; compiled runtime fresh admit each transition | Synthetic composed positive/changed checks pass R01. Live v3 target identity, change and repair path remain open |
| Scope, expiry, cancellation, bounded execution, uncertain delivery, no replay, verified release | runtime/core_v1/compiled_gui.py; test_compiled_admission_*, test_compiled_clock_custody, test_compiled_release_recovery_*, test_compiled_invalid_delivery_reconciliation, test_compiled_unverified_release_reconciliation | 17 compiled-runtime modules plus caller suite pass normal/-O in R01; production adapters still own real I/O deadlines and release evidence |
| Intermediate feedback changes later action | COMPILED_GUI_INTERFACE_V1.md; live mechanics V5; new caller-v3 composition test | R01 proves synthetic v3-to-runtime composition; V5 proves live Chromium mechanics only through caller v2. Repeat on chosen v3 bundle before economics claims |
| Effect and evidence custody | Caller v3 _effect_receipt; test_effect_evidence_reference_survives_outer_receipt; compiled internal action checks; V5 independent POST oracle | R01 keeps the outer task score separate from internal program completion, but uses fixtures. Live retained evidence/retrieval through current caller is missing |
| #12/#46 and comparison integrity | integrated_efficiency_protocol_v1.py validator/evaluator and historical three-arm packet | Historical result is one older-source allocation. The current live matched report, matching settings/capabilities and cold/warm/invalidation/repair costs are missing |

## R01 composition evidence

research/integration/issue57_adaptive_caller_compiled_gui_composition_r01_20261123/RESULT.md composes the full cold adaptive caller v3 accounting path with two bounded local actions. The positive case reports two model attempts, two evidence-selected transitions, zero internal frontier resumptions and a separate independent synthetic task score. The changed-intermediate case retains one action and release, refuses second admission/input, and returns EXECUTION_INCOMPLETE / unknown_state / confirmed_partial.

The composition suite, caller v3 suite and 17 compiled-runtime custody/ordering/release modules pass 132/132 normally and 132/132 under -O. This closes only an offline composition seam. No real provider, app, allocation, task effect or efficiency comparison was run.

## Next finite live path

Reuse the existing independently scored Chromium form workflow and its V5 mechanics rather than inventing a new benchmark family. V5 already demonstrates a live positive two-action method, a changed-page safe stop, schema-preflight handling and independent POST scoring, but it uses caller v2 and has no plain/current/compiled matched comparison. Do not quote its single-pair timing or two-call token total as a treatment effect.

Before freezing a matched allocation, add the v3 execute/evidence adapter to the established workflow and prove exact target/generation binding, retained captures, usage joins, independent POST score, verified release and cleanup on that exact current source. Then freeze one finite plain/current-non-symbolic/compiled schedule including cold acquisition, warm reuse, changed dependency, bounded repair, order, all attempts, stopping rule and full lifecycle endpoints. Preserve failures and unknowns. The live comparison remains HOLD until those prerequisites pass.

#57, #58 and #59 stay open. #59 real-time threat exposure remains a separate priority; no package or MAP01 claim follows from this composition result.
