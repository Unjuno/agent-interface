# Issue #7424 T0: bumpless receiver initialization

**Result: `METHOD_PASS_SCOPED` for the frozen scalar construction only.** Conditioning the receiving route from the current applied input reduced first-applied-input discontinuity from 0.20 to 0.00 normalized units in each of the two eligible cases (100% in this deterministic model). Saturation at the actuator ceiling produced 0.00 discontinuity for both routes and no contrast. The three corrupted-control mutations were detected, stale/missing/revoked state gated the receiver, and the delayed transfer recorded source quiescence before acceptance and actuation.

This does not validate an Agent Interface runtime, a physical actuator, a game, a GUI, model output, useful task progress, or general safety. The receiver is a fixed proportional law with a held additive state offset. A posthoc saved-input calculation found mixed integral absolute tracking-error effects and slightly worse final error for the conditioned route in both nonsaturated cases (0.3556 vs 0.3333); only the initial command-continuity gate was preregistered as the efficacy endpoint. This is a construction result and a reason to include a dynamic receiver-state update in any later test.

## H / T / D / C / U

- **H:** For known-mapping continuous control in this scalar model, initializing the receiver from fresh, actually applied actuator input reduces the first authorized applied-input jump by at least 25% versus cold start without crossing the modeled state bound.
- **T:** Deterministic scalar plant `y[k+1] = y[k] + 0.25 (u[k] - y[k])`, normalized actuator/state in `[0,1]`, output slew at most `0.2` per tick, `ref=1`, `Kp=2`, 20 transitions. Eligible cases: `(y,u)=(0.4,0.6)` and `(0.5,0.6)`. Also run the saturation corner `(0.5,1.0)`, stale/missing/revoked/pre-quiescence denials, a two-tick delayed handoff, and mutations for stale-state acceptance, actuation before quiescence, and initialization from requested instead of applied input. A separately implemented oracle compared each saved numerical route against the equations.
- **D:** Frozen threshold was at least 25% lower discontinuity in each eligible case; all route state maxima at most 1; denied controls produce no receiver actuation; delayed transfer order is quiescence → acceptance → actuation; all three mutations exhibit a detectable violation. Saved-trace audits met these conditions.
- **C:** Saturation can hide an initial-output difference. A command jump may not improve tracking or task value. Cold start may track faster; a held offset may need to unwind. Model dynamics may not describe real GUI/game control.
- **U:** No real backend, sensing delay/noise, semantic planner, app, model, or actuator was used. No real resource enforcement claim is made for the configured memory cap.

## Measurements

| Case | Cold jump | Conditioned jump | Reduction | Cold peak tracking error | Conditioned peak tracking error | Cold final error | Conditioned final error |
|---|---:|---:|---:|---:|---:|---:|---:|
| No disturbance | 0.20 | 0.00 | 100% | 0.60 | 0.60 | 0.3333 | 0.3556 |
| Step at switch | 0.20 | 0.00 | 100% | 0.50 | 0.50 | 0.3333 | 0.3556 |
| Saturated at switch | 0.00 | 0.00 | n/a | 0.50 | 0.50 | 0.3333 | 0.2222 |

Tracking-error peaks include the starting sample, which is the maximum for both nonsaturated cases. The posthoc sum of absolute error across 21 samples was 7.4722 cold vs 7.4370 conditioned (no disturbance), 7.2889 vs 7.4370 (step disturbance), and 7.2056 vs 4.8148 (saturated). These posthoc figures did not change the frozen decision.

## Symbols and units

| Symbol | Meaning | Unit/range | Type |
|---|---|---|---|
| `y` | Scalar plant state | normalized full-scale, `[0,1]` | float |
| `ref` | Reference state | normalized full-scale, `[0,1]` | float |
| `u` | Applied actuator input | normalized full-scale, `[0,1]` | float |
| `Kp` | Proportional gain | dimensionless | float |
| `alpha=0.25` | Discrete plant response coefficient | per tick | float |
| `delta=0.2` | Maximum output change | normalized units/tick | float |
| `k` | Discrete sample index | tick, `0..20` | integer |
| `z` | Receiver additive state offset | normalized actuator units | float |

## Execution and provenance

A02 was frozen at `2026-10-04T05:55:40Z` as `ISSUE7424-BUMPLESS-T0-20261004-A02`. Candidate: one WSLc container invocation, Python 3.12.15, WSLc 3.0.1 / kernel 6.18.40.1-microsoft-standard-WSL2, cached image RepoDigest `python@sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016`, `--pull never`, network none, one CPU, configured memory 256 MiB, readonly `/src`, separate `/out`. The host warned that swap-limit capabilities/cgroup are unavailable; memory enforcement was not independently verified. The A02 candidate exited 0 at 05:55:57Z. Audits and posthoc analysis used saved raw only; no candidate rerun. `AUDIT-v2` and `AUDIT-v4` preserve audit-authoring failures; repaired audits passed. Posthoc invocations v1 and v2 stopped on command construction errors; v3 completed and did not rerun the candidate.

A01's wrong image reference caused a pre-process STOP; see `attempt01-stop/`. Its exact original runner bytes were not retained after later corrections, so A01 provenance is incomplete and is not counted as a scientific result.

Reproduce A02 candidate: see `candidate-command.txt`. Reproduce the independent saved-trace audit: `audit-independent-v5.py` over `candidate-RAW.json`. Verify package bytes with `SHA256SUMS.txt`.
