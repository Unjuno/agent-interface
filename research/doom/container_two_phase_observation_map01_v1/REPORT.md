# Real MAP01 two-phase observation publication transfer v1

Status: **PROMOTE_TO_REAL_INTEGRATION_CANDIDATE_NOT_SHARED_RUNTIME**.

## Question

Can the simple-fixture two-phase observation candidate transfer to the retained real ViZDoom/X11 MAP01 path without changing policy, scorer, model behavior, fixture, key or target hold duration?

The candidate changes only the final sampling window of one ordinary 50 ms `d` hold. Raw capture and typed evidence stay before release; when the remaining hold interval is <=50 ms, durable wire/AIT/PNG publication is deferred until after physical key release. The ordinary post-release observation remains.

## Evidence base

- immutable runtime source bundle: `9e6d5ecdbb5440fd5df1883161f2c63b2c3bb245`;
- ViZDoom 1.3.0 / Freedoom MAP01 / retained `map01-threat-contact-v2` save fixture / skill 1;
- CPython 3.13.5, Linux 6.18.44 x86_64, AMD EPYC 9V74 80-Core Processor;
- private Xvfb/Openbox; zero model calls;
- three fresh matched pairs, seeds 993101..993103, balanced order; no retry.

Construction evidence is excluded: one 250 ms pair showed no baseline overshoot and did not trigger the split; one 50 ms pair reproduced overshoot and triggered it. The formal allocation therefore freezes only the 50 ms condition known to exercise the mechanism.

## Result

| Pair | Baseline upper | Candidate upper | Reduction |
|---|---:|---:|---:|
| 1 | 64.645 ms | 53.637 ms | 11.008 ms |
| 2 | 70.658 ms | 50.859 ms | 19.800 ms |
| 3 | 118.850 ms | 50.900 ms | 67.950 ms |

Baseline retained-input upper median: **70.658 ms**. Candidate median: **50.900 ms**. Paired reduction median: **19.800 ms**, range **11.008–67.950 ms**.

All preregistered hard gates pass:

- terminal scorer agreement: 6/6;
- verified empty release: 6/6;
- scorer missed periods: 0;
- controller-visible scorer leaks: 0;
- candidate split used exactly once in all 3 cases;
- candidate release completes before its deferred artifact publication in all 3 cases.

In baseline cases, the closest full observation artifact becomes ready only **0.221–0.384 ms before release begins**, while capture-to-release is **59.842–101.622 ms**. This independently confirms the current capture-coupled ordering targeted by the candidate.

## Decision

**Promote to a separately versioned real integration candidate, not to shared runtime.** The mechanism transfers from the rendered fixture to real MAP01 mechanics and reduces short-hold capture-coupled retention. It does not establish navigation/combat efficacy, model-wait benefit, population reliability, hard real-time behavior, or superiority to the separately retained owner-deadline scheduled-cutoff mechanism.

Owner deadline and this candidate solve different boundaries: owner deadline ends authority independently of worker completion for predeclared cutoff; two-phase observation keeps ordinary observation acquisition while moving durable publication outside the input-authority critical path.

## Next one-variable gate

Apply the same ordering to one existing recovery/planner-wait integration path **without changing owner deadline, policy, scorer, planner or model**. Compare observation availability and useful-control lifecycle, not merely physical release. If the existing dual-lifetime owner mechanism already makes publication order irrelevant at that layer, retain that negative result and do not add another runtime abstraction.

## Scope

Development mechanics transfer only; no gameplay efficacy/model/planner/human-speed/shared-runtime claim.
