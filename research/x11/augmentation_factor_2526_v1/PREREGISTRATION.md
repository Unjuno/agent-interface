# Factor-isolated X11 augmentation ablation — preregistration

Issue #2526; successor to #2394. The parent failure remains historical and is not rewritten or pooled as a primary result.

## H/T/D/C/U

**H.** With the fixed 354-parameter CNN, source-bound fixtures, fixed seed policy, and equalized training-row budget, isolating translation-only and Gaussian-noise-only augmentation will identify whether the parent degradation is attributable to translation, noise, their interaction, or the changed augmented distribution.

**T.** Four arms, each trained once: untouched baseline; translation-only; noise-only; combined translation+noise. Freeze source manifests, arm order, augmentation parameters, seed, class balance, row budget, and the unchanged 160-row shift plus 160-row base evaluation manifests before reading outcomes. No threshold tuning.

**D.** Retain source/manifest hashes, arm parameters, training receipts, per-row confidence and route, labels, accepted true/false rows, YIELD/reject counts, corruption controls, and independent recomputation. Run in one pinned container invocation; no rerun, replacement, or post-result arm selection.

**C.** PASS_AUGMENTATION_FACTOR_ABLATION_SCOPED requires all arms complete, exact integrity, independent audit pass, zero accepted false positives, and any benefit supported by matched baseline comparison. FAIL_AUGMENTATION_FALSE_ACCEPT on any accepted false positive. HOLD_AUGMENTATION_NO_SAFE_BENEFIT if no non-baseline arm yields safe coverage/correctness benefit. HOLD_AUGMENTATION_FACTOR_UNIDENTIFIABLE if arm differences cannot isolate a cause.

**U.** This is a finite fixture ablation only. It does not establish arbitrary-GUI transfer, model quality, domain generalization, runtime utility, gameplay, or production promotion.

## Collision and stop policy

Use only `research/x11/augmentation_factor_2526_v1/**` on branch `research/x11-augmentation-factor-2526-v1`. Do not modify #2394 or its evidence, and stop after the first formal result or an explicit construction/infrastructure stop.