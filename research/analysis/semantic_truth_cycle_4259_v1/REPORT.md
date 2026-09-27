# Cyclic semantic truth-maintenance — Issue #4279

Allocation: `semantic-truth-cycle-4279-20260923-01`

## Result

**PASS_CYCLIC_TRUTH_RETRACTION_SCOPED**.

One prospectively source-frozen formal invocation completed. Reruns/replacements/post-result tuning: 0/0/0.

- formal rows: 12;
- candidate/oracle mismatches: 0;
- unsupported candidate TRUE facts: 0;
- candidate affected-region recomputations: 25;
- global recomputation comparator: 48;
- naive immediate-support comparator stale TRUE witnesses: 9;
- anchor FALSE/UNKNOWN controls retract A/B/C from TRUE;
- fresh anchor restoration rederives the component;
- unrelated-only mutations never recompute A/B/C;
- macro readiness matches independent oracle throughout;
- authority: none;
- independent audit errors=[];
- copied-evidence corruption controls: 12/12 rejected;
- runner/audit/controls exits: 0/0/0.

The core counterexample is a cached A<->B cycle. `LOCAL_SUPPORT_RETAIN` can keep A TRUE because B is TRUE and B TRUE because A is TRUE after the external `anchor` is removed. The candidate does not accept that circular justification: it re-grounds the affected SCC/downstream region from current base facts and therefore retracts A/B/C until a fresh anchor returns.

This is a finite authored support graph. It does not establish hidden dependency completeness, neural-model causality, arbitrary negation-cycle semantics, GUI/task benefit or runtime authority.

## Chronology / integrity

Excluded construction initially exposed one corruption-control weakness: deleting only one stale naive witness still satisfied the predeclared `>=2` discriminator. Before source freeze, the auditor was strengthened to bind the retained stale-witness list and the mutation was changed to remove all stale witnesses. Construction then passed audit plus 12/12 controls. No formal row had run.

Preformal GitHub transfer also caught one manual `model.py` transcription mismatch (two comments omitted). Formal rows remained 0. Exact frozen bytes were restored and all Git blobs read back before formal authorization.

Formal raw SHA-256: `bf4c7e11c8aca81d214cf597a6682813acd0209730331770fb5787f5399e4ced`.
Audit stdout SHA-256: `575ba987f151e5e923595247f8e6f1d3e49f7073d44330b927cffef48be772ab`.
Controls stdout SHA-256: `7df6117e6b3b1a05ad0ce060ccb9ffde8ca93f5fb022ee79bf4b69b1caa8489b`.
Freeze SHA-256: `8a3261334cc34b0474290775279c699d10f8a12f90fe81eb53d45e50f018e4ba`.
