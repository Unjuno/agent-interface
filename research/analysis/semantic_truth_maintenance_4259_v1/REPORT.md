# Semantic truth maintenance — Issue #4259 formal result

Allocation: `semantic-truth-maintenance-4259-20260923-01`  
Disposition: **PASS_SEMANTIC_TRUTH_MAINTENANCE_SCOPED**

## Result

One prospectively source-frozen formal invocation completed with 28 raw policy-step rows. Formal reruns/replacements/post-result tuning: 0.

| policy | total derived-fact recomputations |
|---|---:|
| GLOBAL_INVALIDATE | 84 |
| SUPPORT_SET_RETRACTION | 51 |

Support-set retraction reduced the frozen recomputation count by 33 (39.3%) while preserving the exact oracle three-valued lattice and `macro_ready` result at every step.

Directed gates passed:
- unrelated `unrelated_theme` mutation caused zero support-policy derived recomputation;
- target identity invalidation retracted the primary path while the verified-handle alternate support kept `can_submit=TRUE`;
- producer-generation reset made vision facts UNKNOWN and propagated the exact oracle state;
- focus UNKNOWN propagated `macro_ready=UNKNOWN` rather than unsafe TRUE/FALSE coercion;
- restoration in a new generation recovered the exact lattice;
- every retained provenance record reconstructed its structural base support and generation/value state;
- every row retained `authority=none`.

Independent raw-only auditor: errors=[]; 12/12 coherent copied-evidence corruptions rejected.

## H/T/D/C/U boundary

H/T/D/C/U are frozen in PLAN.md and FREEZE.json. The result supports only the finite authored dependency graph. It does not establish that neural/model predicates expose complete dependencies, that support graphs are cheaper in wall time, or that derived facts may grant execution authority.

No GUI, OS input, provider/model, network experiment, latency/token benefit, runtime promotion or product claim.
