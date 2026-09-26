# CEGIS grammar-gap detection v1 — Issue #4294

Allocation: `cegis-grammar-gap-4294-20260923-01`

## H
When a fixed skill grammar omits a predicate required by the oracle, accumulated counterexamples can expose an irreducible visible-feature alias. An alias-aware CEGIS loop should return `GRAMMAR_INSUFFICIENT` and emit no executable candidate rather than overfit or drop evidence. A matched complete grammar must remain synthesizable.

## T
Deterministic CPython stdlib fixture. Oracle state has six booleans; the incomplete grammar sees only five and cannot inspect `approval_token`. COMPLETE_CONTROL adds one preregistered PRIMARY rule that may inspect approval_token. Initial examples, verifier IDs, held-out nuisance-shift IDs, template ordering, search tie-break, 6-round/6-rule budgets and oracle are frozen. The verifier exhausts all 64 semantic states at nuisance=0; held-out is the same 64 semantic states at nuisance=1, so held-out tests nuisance invariance rather than introducing unverified semantic combinations. Compare BLIND_BUDGETED_CEGIS vs ALIAS_AWARE_CEGIS under both grammars. Construction uses development-only states not present in formal IDs.

## D
PASS_CEGIS_GRAMMAR_GAP_DETECTION_SCOPED iff incomplete alias-aware detects the exact conflicting retained pair within <=6 verifier rounds, emits no executable candidate after detection and preserves prior examples; incomplete blind never claims COMPLETE; complete-control alias-aware and blind both reach COMPLETE within budget with held-out accuracy 1.0; false grammar-gap on complete control=0; alias-aware unsafe action on oracle-YIELD states=0; authority=false; raw audit errors=[]; >=10 coherent corruptions reject; formal invocations/reruns/replacements/tuning=1/0/0/0.

## C
This detects insufficiency relative to a declared finite feature grammar. It does not discover the semantics of the missing predicate. The authored finite fixture makes aliasing exact.

## U
No GUI/model/provider/input, automatic predicate invention, runtime authority, latency/token benefit or production synthesis claim.
