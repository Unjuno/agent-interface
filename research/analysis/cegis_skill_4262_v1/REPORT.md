# Counterexample-guided bounded skill synthesis — Issue #4262 formal result

Allocation: `cegis-skill-4262-20260923-01`  
Disposition: **PASS_CEGIS_SKILL_SYNTHESIS_SCOPED**

## Result

One prospectively source-frozen formal invocation completed. Formal reruns/replacements/post-result tuning: 0.

The one-shot and CEGIS arms use the same exhaustive deterministic synthesizer and the same fixed six-rule grammar. The only treatment difference is that CEGIS adds the lowest-ID verifier mismatch and resynthesizes.

| endpoint | ONE_SHOT | CEGIS |
|---|---:|---:|
| held-out correct | 5/16 | **16/16** |
| action on oracle-YIELD states (all 64 states) | 45 | **0** |
| final rule count | 2 | 6 |
| verifier counterexamples consumed | 0 | 5 |

CEGIS counterexamples were exactly `[1, 17, 7, 30, 51]`. The final six-rule list is the frozen grammar in the discovered safe order: forbidden-YIELD, stale-YIELD, ambiguous-YIELD, missing-evidence-YIELD, primary action, alternate action. Every accumulated counterexample remains correct in the final candidate.

Independent raw audit: errors=[] over 128 arm/state rows. Twelve coherent copied-evidence corruptions were rejected. Frozen scientific source hashes after formal exactly match `FREEZE.json`.

## Construction/audit chronology

Excluded construction used the same scientific runner/oracle/synthesizer and produced the same qualitative endpoint. The original auditor passed the unmodified construction raw, but its first corruption-control harness raised `KeyError` when a deliberately dropped row was presented. That preformal auditor limitation and exact old source/raw/audit are retained under `construction_history/01/`.

Before any formal invocation, only the auditor was changed so a missing CEGIS row is reported as an audit error instead of indexing the absent row. The scientific runner, oracle, grammar, split, synthesizer and decision thresholds were unchanged. The same construction raw then passed the repaired audit and 12/12 mutation controls. Formal execution began only after those exact repaired bytes were publicly frozen on GitHub.

## H/T/D/C/U boundary

The full H/T/D/C/U is retained in `PLAN.md` / `FREEZE.json`.

This result shows that explicit counterexamples can guide search to a correct rule ordering inside one finite grammar whose predicates already contain all required semantic concepts. It does **not** show automatic discovery of missing predicates, natural GUI generalization, model-generated skill quality, live authority, latency/token benefit, or product readiness. The synthesized skill remains authority-neutral evidence only.
