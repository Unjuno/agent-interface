# Operation/target ID-invariant target-admissibility result

Decision: **PASS_TARGET_ADMISSIBILITY_RESOLVES_ID_INVARIANT_ALIAS_SCOPED**.

Task `OPERATION-TARGET-ID-INVARIANT-TARGET-ADMISSIBILITY-20260918-001` executed one deterministic primary replay over the exact 96-row #1133 corpus after source-first freeze/readback and ownership reread. Primary invocations1; reruns0.

## Frozen findings
- parent semantic digest reproduced exactly: `ea4a86baf3d2efc6f79f75703ef164d2c830cd3f5634e7ad057c26315da752dd`;
- parent #1166 ID-invariant conflicting groups: **28**;
- augmented representation conflicting groups: **0**;
- augmented feature: exactly one categorical `target_admissibility` in `{NOT_REQUIRED,MISSING,AMBIGUOUS,STALE,CURRENT}`;
- derivation inputs only: pre-decision `requires_target`, `targets`, `ambiguous`, `hard_invalid`;
- opaque observation-ID leakage: 0;
- opaque target-ID leakage: 0;
- authority grants: 0;
- row count / acceptable dispositions unchanged: 96 / unchanged;
- independent audit: PASS, errors `[]`;
- copied-result corruption controls: 4/4 rejected;
- frozen source rehash: all exact.

## Interpretation
The #1166 collision is not evidence that opaque IDs must be model features. In this authored corpus, one typed current-target admission semantic is sufficient to distinguish the recurring `CLICK_MULTI↔AMBIGUOUS_TARGET`, `NO_LOCAL_ACTION↔MISSING_TARGET`, and `CLICK_UNIQUE↔STALE_STATE` cases while keeping observation/target IDs out of the semantic signature.

This does **not** prove that the representation is sufficient on real retained states or that a learned backend is needed. The next high-information gate is a fresh retained/real-data collision census using the same ID-invariant packet plus this frozen target-admissibility field. Do not allocate a model merely because this synthetic corpus is now collision-free.
