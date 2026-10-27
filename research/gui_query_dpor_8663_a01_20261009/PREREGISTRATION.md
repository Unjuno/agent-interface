# Predicate-aware DPOR T0 — A01

Allocation: `GUI-QUERY-DPOR-8663-A01-20261009`  
Base: `743ae74ec5be2472ff27fa06fe13d5ecf8534de5`  
Scope: deterministic, finite CPU model only. No GUI, model/API, network, input, or shared runtime.

## Question and model

Compare exhaustive linearization, node-footprint sleep-set reduction, and predicate-aware sleep-set reduction on a frozen UI query model. A query selects visible, enabled nodes named `Save` in the active scope. Each scenario has one to three UI nodes and at most four UI transitions, plus the ordered `query -> validate -> admit` control events. Fixtures cover a safe unique target, empty and multiple sets, matching insertion/removal, rename and enablement membership changes, modal scope replacement, incomplete/unknown enumeration, ABA membership change, and four commuting unrelated transitions. The unrelated fields are outside the selector predicate.

The node-only dependency rule sees concrete query-result node identities and versions, but omits selector scope, completeness, and unreturned-node membership. The predicate-aware rule conservatively makes every possible membership, scope, completeness, or unknown transition dependent with query/validation/admission. Unknown is always dependent. Sleep-set DFS uses the frozen event order for deterministic representatives.

The model oracle marks reuse of the original selection invalid when its predicate epoch, scope, completeness, exact member set, or selected-node version changed between query and admission. `NODE_ONLY` intentionally ignores set-level invalidation; `PREDICATE_CERT` requires the original certificate to remain unchanged; `ALWAYS_REQUERY` selects from a complete, unique set at admission. This is a finite test contract, not a production UI-safety claim.

## Hypothesis and decision rule

H: predicate-aware reduction preserves the exhaustive set of typed final outcomes and unsafe-admission classes in every fixture, while reducing at least 20% of exhaustive schedules in the four-transition commuting control. Node-only reduction will omit at least one planted stale-selection witness. The expected result is empirical; no benefit is presumed.

PASS only if the independent raw-only auditor reconstructs the exhaustive schedule set, confirms exact predicate-DPOR outcome and unsafe-class coverage, finds replayable witnesses for each unsafe class, confirms unknown events remain dependent, catches the three under-dependency mutants (missing predicate, cross-scope, unknown), and verifies at least 20% reduction on the commuting control. Otherwise record the matching scoped FAIL or HOLD. A test never grants action authority or qualifies a live adapter.

## Execution controls

The model, candidate, auditor, construction checks, and this preregistration are hashed into `FREEZE.json` before the candidate is invoked. Run exactly one candidate and one independent auditor. Preserve first outputs and all failures. The auditor imports no candidate code and replays raw schedules using a separate implementation. No formal candidate retry is allowed.

## Limitations

Soundness is limited to the declared finite transition system and sleep-set independence contract. The model cannot establish accessibility-tree/DOM/native enumeration completeness, atomic GUI snapshots, timing coverage, live task success, or product safety. The unchanged/unrelated controls can show only that these modeled event commutations exist.
