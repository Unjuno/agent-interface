# Tiny predicate specialist — Issue #4218 formal result

Allocation: `tiny-predicate-specialist-4218-20260923-01`  
Disposition: **PASS_TINY_PREDICATE_SPECIALIST_SCOPED**

## Result

One prospectively source-frozen formal invocation completed. No reruns, replacements, exclusions or post-result tuning.

- support rows: 32
- held-out nuisance-shift rows: 256
- TARGET_CORRECT accuracy: 256/256
- UNKNOWN recall: 128/128
- false executable TRUE/FALSE on UNKNOWN: 0
- downstream graph terminal equality: 256/256
- specialist artifact: 107 bytes
- general six-predicate median warm call: 942.651 ns
- specialist median warm call: 216.244 ns
- specialist/general timing ratio: 0.229400
- independent raw-only audit: `PASS_TINY_PREDICATE_SPECIALIST_SCOPED`, errors=[]
- coherent corruption controls rejected: 11/12 (frozen gate >=10)

The one unrejected corruption was `duplicate_row`. The frozen control harness therefore reports its own stricter `pass=false`, while the preregistered decision gate requires at least 10 coherent corruptions to reject and is satisfied at 11/12. This miss is retained as an audit-coverage limitation and is not repaired by rerunning or rewriting the consumed formal result.

## Interpretation

The tiny specialist exactly preserved the parent three-valued TARGET_CORRECT semantics and all 256 downstream graph terminals while its Python warm-call median was about 22.9% of the full six-predicate batch evaluation. This supports only the scoped statement that a repeatedly reused predicate can be specialized into a much smaller local evaluator in this authored finite representation.

The specialist learned a four-entry lookup from 32 support rows. A deterministic hand-authored rule is arguably simpler, and the parent #4215 backend itself is authored linear logic rather than Laya/Kev or another learned semantic model. Therefore this result is not evidence that model distillation is generally worthwhile, nor that the measured sub-microsecond Python timing ratio predicts production model latency.

## Scope

No GUI, OS input, authority, model/provider, network experiment, Astra labeling cost, natural semantic distribution, cross-domain transfer, token benefit or product/runtime promotion. #4218 remains a one-predicate component result only.
