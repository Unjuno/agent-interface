# MAP01 repeated no-progress bounded deoptimization v2

Decision: **PASS_BOUNDED_DEOPT_COVERAGE / PASS_AUDIT**.

V1 retained one completed case then stopped when the outer two-case command timed out during case 1; V1 has no scientific disposition and is not pooled. V2 changes only outer orchestration (one case per tool call), uses new seeds, and keeps the frozen policy/thresholds unchanged.

In a no-monsters diagnostic MAP01 environment, both arms run 45 X11-screen-driven decisions. Every decision attempts 350 ms forward. A visual normalized-descriptor MSE below 0.055 is `no_progress`, followed by `use`. Baseline always applies one 190 ms right-turn pulse. Candidate uses the same small repair unless another no-progress occurs within four decisions; then that repair alone expands to six identical 190 ms right-turn pulses. Controller action selection receives no position, angle, automap, sector/object labels, pause/save state or direct game action vectors.

Independent scorer result across four matched seeds:

- coverage 64-unit cell deltas candidate-baseline: +11, +7, +6, +10; paired median **+8.5 cells**;
- candidate coverage >= baseline: 4/4 pairs;
- candidate revisit fraction <= baseline: 4/4 pairs;
- candidate escalation exposed: 4/4 runs;
- release failures: 0/8; deaths: 0/8;
- map exits: 0/8.

The independent audit recomputes every no-progress classification from retained descriptor arrays, validates baseline/candidate repair pulse contracts, recomputes coverage/revisit/path length from evaluator-only trajectories, and rechecks all InputOwner release records.

Interpretation is narrow: repeated failure of the same small local repair can justify a larger still-bounded deoptimization envelope instead of retrying the same correction. This improved exploration coverage in this isolated no-monsters fixture. It does not establish normal-combat benefit, stage clear, model efficacy, general navigation superiority, or permission to expose hidden pose to a controller. The next transfer must reintroduce normal MAP01 hazards while holding this repair rule fixed, and should remain separate from active recovery/context-validity work.
