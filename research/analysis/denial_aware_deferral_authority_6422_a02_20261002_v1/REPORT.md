# A02 result — conditional-deferral authority boundary

**Status: `PASS_METHOD_SCOPED` with a retained audit-report metadata defect.** This is a finite synthetic no-effect result, not completion of all #6422 T0.

The eight-row fixture was independently reconstructed. A01's eligibility rule would ask for a fresh approval in all three cases with an otherwise valid condition receipt but an observer, unmapped principal, or missing required-principal mapping. The guarded rule held all three. It also held wrong predicate, agent-asserted condition, wrong evidence kind, and condition-not-source-stated. The one authorized, source-stated, independently verified condition remained eligible for a clearly fresh approval request. All eight rows retained `effect_authorized=false`. Five raw corruption controls were rejected.

This supports the narrow hypothesis that deferral eligibility must bind the stated condition to an authorized required principal; valid-looking condition evidence alone is insufficient. It does not demonstrate that a real implementation follows this rule, that re-asks decrease in model conversations, or that users benefit. The finite block does not cover the complete interruption-budget requirement or all T0 pairs, so A02 is a successor boundary result, not full T0 completion and not a basis for T1.

Evidence caveat: `audit_report.json` says eight rows were reconstructed and records zero errors, but its free-text `scope` field incorrectly says “six” cases. That exact formal output is preserved unchanged. The free-text defect does not change its row-count field or per-row decision checks, but reduces report polish; see `BUILD_HISTORY.md`. No post-run editing or rerun was used to conceal it.

Formal local work: candidate once, raw-only auditor once, retries zero; 3 host construction tests passed. Windows host CPU, CPython 3.11.9. No model, person, GUI, WSLc, Docker, GPU, CUDA, live approval, or effect.
