# Latency-aware early-exit tiny System-1 — retained first outcome

Issue #889. Task `LOCAL-SYSTEM1-LATENCY-AWARE-EARLY-EXIT-20260917-001`.

## Allocation chronology

- **A1**: source-first frozen monolithic 8-cell runner. First formal invocation exceeded the outer container execution budget before producing any scored output. Retained permanently as `STOPPED_FORMAL_OUTER_TIMEOUT`; not pooled and never rerun.
- **A2**: harness-only repair with fresh case IDs. Scientific model/data/loss/training/timing code remained frozen; only outer dispatch changed to one process per `(seed, arm)` cell. Eight fresh cells completed, reruns 0.

## First scientific disposition

**`HOLD_LATENCY_OBJECTIVE_TRADEOFF_NOT_CLOSED`**.

The fixed compute penalty `lambda=0.15` did **not** produce a different discrete computation policy under the frozen inference gate. For every ordinary and stress evaluation row in both arms, all 2,048 examples exited at depth 2 of 4 (`mean_normalized_compute=0.5`). Thus `compute_better_pairs=0/4`.

Observed warm p95 latency was inconsistent across pairs: latency-aware was faster in 2/4 pairs and slower in 2/4. The preregistered paired median p95 reduction statistic was 10.07%, below the required 20%. Because executed depth was identical, these latency differences are not attributed to learned early exit.

The more important blocker is candidate competence: both arms missed the frozen correctness gate. Ordinary accuracy was 73.5–76.5%; stress accuracy 72.6–74.5%, versus required >=90% / >=80%. Teacher-YIELD -> executable error rates were about 15.6–18.0% ordinary, so this candidate is not safety-promotable regardless of latency.

The latency-aware arm did not materially worsen aggregate accuracy: paired median ordinary loss was -0.146 percentage points (candidate slightly higher), paired median stress loss -0.024 percentage points. But this does not rescue the result because neither arm is competent enough and the compute policy did not change.

## Paired p95 / compute

| seed | accuracy-only p95 ms | latency-aware p95 ms | paired reduction | base compute | candidate compute |
|---:|---:|---:|---:|---:|---:|
| 8891701 | 0.2724 | 0.2829 | -3.84% | 0.50 | 0.50 |
| 8891702 | 0.2760 | 0.4989 | -80.75% | 0.50 | 0.50 |
| 8891703 | 0.3948 | 0.3001 | +23.98% | 0.50 | 0.50 |
| 8891704 | 0.5241 | 0.3972 | +24.20% | 0.50 | 0.50 |

Median p95 by arm (descriptive, not preregistered paired statistic): accuracy-only 0.3354 ms; latency-aware 0.3487 ms.

## Interpretation

This is not evidence that latency-aware learning is ineffective in general. It is evidence against this **specific mechanism** at the frozen settings: a soft expected-depth penalty plus a hard 0.5 halting gate did not alter the realized exit depth. The experiment therefore fails to expose the causal mechanism the user proposed.

Do not sweep `lambda` or the halting threshold inside this allocation. A successor must change the computation/halting hypothesis explicitly, for example by making time-to-correct or measured exit latency directly supervise the halting decision, while retaining deterministic authority and explicit YIELD.

## Integrity / retention

- A2 formal cases: 8; same-case reruns/replacements: 0.
- Independent A2 auditor: PASS, errors `[]`.
- Aggregate RESULT SHA-256: `dda88cd12c517e0cbb68b305826969a376fa9bf72ad6db586f395f003545b8ac`.
- AUDIT SHA-256: `728e606c095bc46a10989a6f370a95809ca57d5f42a1a470acf59848efd54d4c`.
- Complete local A2 evidence archive: 218,666 bytes, SHA-256 `c31053c22aaebbdb28596c89e1df77099d78dde8dc15b6fb88d239b8853333b2`.
- Local manifest SHA-256: `9548a5b96ff956462d1b622443ce8493957d00db501c6ceed781ba13526042eb`.
- Full binary evidence archive is **not GitHub-retained**; GitHub retains source, aggregate result, audit, report and manifest/digests.
- Postformal scientific source SHA-256 remained exact to the premeasurement freeze.

## Scope

Synthetic 64-float structured state; 837,151-parameter PyTorch CPU model; one thread; Xeon Platinum 8370C environment; six executable classes + YIELD. No network, model provider, GUI, task input or authority path. This does not alter #838's retained `HOLD_ACTIVE_LABELS_NOT_SUFFICIENT` and does not establish real computer-use or frontier-boundary benefit.

## Next discriminator

Test a **direct latency-supervised halting mechanism**, not another penalty sweep: train early exits to be correct/confident and train the halt gate against a frozen per-exit latency/correctness target (or straight-through time-to-correct objective), then measure whether realized depth changes. Only after a competent candidate exists should it move to real Astra-authored shadow decisions and compete with rule/linear/tree baselines.
