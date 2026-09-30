# Predicate dependency completeness gate v1 — Issue #4233

Allocation: `predicate-cache-completeness-4233-20260923-01`.

## H
A dependency-scoped semantic cache is safe only if applicability dependencies are complete. An incomplete declared key can false-reuse across a hidden dependency change. A complete declaration prevents that. If completeness is unknown, bypassing cache reuse for that predicate preserves full-recompute semantics while still allowing unrelated complete predicates to cache.

## T
Authority-neutral deterministic CPython standard-library replay. Two predicates over a frozen 12-state trace:
- READY_TO_SUBMIT true deps=(form,risk), intentionally incomplete declared deps=(form), declaration_complete=false.
- TARGET_MATCH true/declared deps=(target), declaration_complete=true.
Three policies: DECLARED_ONLY, COMPLETE_DECLARATION, COMPLETENESS_GATED. Formal denominator 12 states x 3 policies x 2 predicates =72 policy-predicate observations. Trace covers unrelated change, hidden risk flip, hidden risk ABA with new generation, form change, hidden change with coincidentally unchanged output, target change, source generation, intent version, producer version. One formal invocation; reruns/replacements/exclusions/tuning=0.

## D
PASS_DEPENDENCY_COMPLETENESS_GATE_SCOPED iff DECLARED_ONLY exposes >=1 semantic mismatch and >=1 hidden-dependency false reuse; COMPLETE_DECLARATION and COMPLETENESS_GATED have predicate/graph mismatch0; gated READY has zero cache hits while complete TARGET_MATCH retains >=1 hit; complete READY has >=1 safe unrelated-change hit; ABA new hidden generation is never credited as valid hit by safe policies; source/intent/producer changes invalidate; authority=false; independent raw audit errors=[]; >=10 coherent evidence mutations reject; formal1/reruns0/replacements0/tuning0.

## C
Authored deterministic semantics and true dependency relation. This tests consequences of completeness, not automatic hidden-dependency discovery. DECLARED_ONLY is a negative control, not a production allegation.

## U
No learned model, real GUI coupling, dynamic dependency discovery, cross-session reuse, token savings, natural invalidation frequencies, live authority, task success or production integration.
