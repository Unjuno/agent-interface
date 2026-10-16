# Constrained interaction-fault diagnosis

## Four distinct endpoints

### Detection sensitivity — #5330

Merged [PR #5351](https://github.com/Unjuno/agent-interface/pull/5351) retains `PASS_DESIGN_SENSITIVITY_ONLY` on its exact planted synthetic model: constrained pairwise/three-way designs were tested for finding predeclared interaction hazards. This is a detection result, not a claim that the resulting test outcomes uniquely identify which modeled fault set is present. The separate supplemental STOP/audit history remains preserved; no real GUI/model/runtime safety claim follows.

### Fault-set diagnosability — #8894

**Status:** Open, unverified successor to #5330. The question is whether legal test rows yield distinct pass/fail signatures for each registered fault set, and which distinct fault sets are observationally indistinguishable under the constraints. A method can pass while the proposed diagnosability advantage is unsupported; the Issue distinguishes method integrity from the scientific hypothesis. It must reuse retained #5330 fixture definitions without rerunning or reinterpreting that consumed candidate allocation. See [Issue #8894](https://github.com/Unjuno/agent-interface/issues/8894).

### Adaptive versus fixed plans — #8895

**Status:** Open, unverified successor to #8894. Compare an outcome-dependent decision tree with the best fixed suite/order for the same finite fault grammar and constraints. The fixed suite may stop early when its observed prefix uniquely identifies a fault set; compare against an exhaustively searched best-fixed baseline, not an arbitrary suite. Report executed configurations, adaptive sequential rounds, fixed-suite makespan under a preregistered worker cap, and test/reset/communication costs. If those costs cannot be supported, show a tests-versus-rounds/parallelism Pareto frontier and do not call fewer tests “faster.” See [Issue #8895](https://github.com/Unjuno/agent-interface/issues/8895).

### Outcome-signature corruption robustness — #8898

The already indexed #8898 successor asks whether signatures remain diagnosable after a bounded number of corrupted outcomes. It is a robustness layer over declared signatures, not a substitute for establishing that the underlying fault sets are distinguishable. Keep ambiguity when corruption exceeds separability.

## Scope boundary

Constrained locating arrays, adaptive fault localization, and corruption-tolerant codes are established methods in their source domains. These Issues propose finite repository-specific comparisons; they do not estimate real fault prevalence, prove product fault localization, or authorize runtime interventions. Safe-probe constraints from adjacent #6147 remain separate and must not be weakened.
