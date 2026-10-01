# Normal-MAP01 repeated no-progress bounded deoptimization transfer v1

## Decision

**PASS_NORMAL_MAP01_DEOPT_TRANSFER / PASS_AUDIT**.

This allocation transfers the navigation-only bounded deoptimization rule retained under Issue #557 from a no-monsters diagnostic into normal MAP01 with monsters present. No ATTACK input, model call, recovery cover or hidden state is added to the policy. Navigation parameters are unchanged.

Four matched seeds, 45 decisions per arm:

| seed | baseline coverage64 | candidate coverage64 | delta | baseline health | candidate health |
|---|---:|---:|---:|---:|---:|
| 991400 | 20 | 30 | +10 | 97 | 97 |
| 991401 | 20 | 25 | +5 | 100 | 88 |
| 991402 | 20 | 28 | +8 | 100 | 96 |
| 991403 | 20 | 28 | +8 | 100 | 100 |

- paired median coverage improvement: **+8.0 64-unit cells**;
- candidate coverage non-worse: 4/4 pairs;
- candidate revisit fraction non-worse: 4/4 pairs;
- candidate escalation exposed: 4/4 runs;
- every candidate final health >= predeclared 80 floor: 4/4;
- deaths: 0/8; release failures: 0/8;
- kills: 0/8; no ATTACK input was available;
- MAP01 exits: 0/8.

The independent audit recomputes visual no-progress classifications from retained descriptor arrays, verifies the small/escalated repair pulse contracts, recomputes coverage/revisit/path length from evaluator-only pose traces, rechecks health/death and all InputOwner release records, then reapplies the preregistered PASS/HOLD/FAIL rule.

## Interpretation

The coverage benefit observed without monsters survives this bounded normal-MAP01 transfer while staying above the predeclared health floor. The result still shows a cost: one candidate run ends at health 88 while its matched baseline remains at 100. PASS therefore means the scoped transfer gates passed; it does not mean exploration is free or that threat-aware navigation is solved.

This is not a MAP01-clear or combat-controller result. The controller never receives pose, health, ammo, kills, map/sector labels or automap; those fields are evaluator-only. No firing policy, model or planner latency is present. The next composition question is how to preserve this deoptimization benefit when threat-aware local control is active, without conflating navigation and recovery-context work already owned elsewhere.
