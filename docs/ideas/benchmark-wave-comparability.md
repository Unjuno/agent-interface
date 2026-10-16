# Benchmark wave comparability — #8885

- **Status:** Unverified transfer and evaluation-method proposal.
- **Source:** [Issue #8885](https://github.com/Unjuno/agent-interface/issues/8885).
- **Idea:** When task forms or task mixes change between benchmark waves and direct pairing is unavailable, test whether fresh, representative anchor-task families support a narrowly defined comparison. Preserve wave-specific outcomes, task-family strata, unknowns, timeouts, and safety outcomes; never reduce safety to a compensating aggregate score.
- **Outcome:** No implementation or result is recorded. This is not a claim that existing benchmark results are invalid or that scores can generally be converted to a common scale.

## Relation to existing work

Direct same-task comparisons remain preferred under [#57](https://github.com/Unjuno/agent-interface/issues/57). The held-out benchmark and oracle contract in [#12](https://github.com/Unjuno/agent-interface/issues/12), visual difficulty calibration in [#6000](https://github.com/Unjuno/agent-interface/issues/6000), human-agent item diagnostics in [#8582](https://github.com/Unjuno/agent-interface/issues/8582), and stratified route estimates in [#5939](https://github.com/Unjuno/agent-interface/issues/5939) answer different questions. In particular, anchor linking must not hide route-by-family interactions or replace per-family results.

## Smallest useful test

Use a finite, deterministic outcome table with multiple task families and waves. Compare raw means, a prespecified task-mix standardization, and an anchor-gated link against a known reference. Include composition-only change, a true route effect, route-by-family interaction, anchor drift, missing family overlap, repeated-item exposure, and unknown/timeout/unsafe rows. An independent raw-only audit must reconstruct every estimand and reject mutations to anchor identity, scorer version, strata, denominator, and safety outcomes.

Emit `NOT_COMPARABLE` or `PARTIAL_LINK_ONLY` when anchor invariance, construct overlap, or the target population cannot be supported. A method-scoped pass would establish sensitivity on the frozen table only; empirical cross-wave comparability requires a separately owned and preregistered study.
