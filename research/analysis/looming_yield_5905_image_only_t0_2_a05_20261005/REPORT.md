# Issue #5905 A05 — all-frame regression-TTC host screen

## Outcome

`EXPLORATORY_NO_INCREMENTAL_VALUE` on this one finite raster fixture. At a zero-false-YIELD frontier, five-frame OLS-TTC cued 6/6 authored approaches, improving on the A03-grid last-interval secant result of 5/6. But endpoint pixel-change and target-area-growth also each cued 6/6. All four methods had zero false cues among the six identifiable controls. Therefore the regression estimator adds no measured value over either simpler baseline here.

The independently reconstructed contact leads after the fixed 0.20 s release latency were 2.4, 2.6, 2.8, 3.0, 3.2, and 3.4 seconds. The raw-identical animation twin produced the same semantic output. The auditor rebuilt all 65 frames, candidate-visible features, gates, metrics, comparator grids, frontiers and contact margins: 13/13 sequences, zero discrepancies. The audit is an independent implementation for this host screen, not a formal allocation audit.

## Hypothesis and method

**H:** A five-frame OLS fit of equivalent target radius against timestamps will reduce last-interval raster quantization enough to beat a two-frame secant TTC comparator at the same observation budget and false-YIELD allowance, while retaining abstention on the detectable controls.

**T:** The immutable A03 observation/truth fixture contains 13 sequences of five 128×128 PGM frames at 100 ms cadence: six centered constant-speed approaches, five assumption-violating controls, a stationary nonlooming hazard, and an observation-identical animation twin. The probe computed `TTC = final equivalent radius / OLS radius slope` with fixed thresholds [1.5, 2, 2.5, 2.8, 3, 4] seconds. Shared trackability was held constant; pixel and growth grids were scored alongside. The twin was excluded from the six identifiable-control FP budget and checked separately.

**D:** Preliminary incremental signal required all six approaches to yield with positive release lead, no cue among identifiable controls, matching twin output, zero independent-audit errors, and a maximum true-positive frontier strictly above both simpler baselines at FP=0. The measured frontier was regression=6, pixel=6, growth=6; therefore the criterion for incremental value failed.

**C:** This is one authored synthetic raster fixture only. FP=0 is not a population rate; marker points are only a camera-scale proxy. No capture/runtime cost, GUI, physical release, task progress, damage or gameplay was measured.

**U:** This was an unregistered host-only exploratory screen after OrbStack's isolated guest could not start nested OCI containers. It is not a preregistered T0, not a container result, and not evidence of live control, agent behavior, safety, or general TTC accuracy. It does not consume or close #59's live allocation.

## Reproduction and retained evidence

- Screen: `PYTHONDONTWRITEBYTECODE=1 python3 regression_probe.py inputs/observations.json.gz inputs/truth.json.gz`
- Independent audit: `PYTHONDONTWRITEBYTECODE=1 python3 audit.py --regression inputs/observations.json.gz inputs/truth.json.gz results/regression_screen.json results/regression_audit.json`
- Local tests: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest -v test_audit test_candidate test_runner test_regression_estimator test_regression_probe test_regression_audit` — 18 passed.
- Raw screen SHA-256: `fb1c9ce268e88e0147858786063da6ec1356358e0aa7172601515724c8dca5b5`.
- Independent audit SHA-256: `f059c5537e25526bd75959a1aa5b752b6332456b2792bb5eb757dc850f54fb1f`.
- The input gzip hashes remain the immutable A03 values recorded in `RUN.json`.

The merged A04 secant pilot uses a different TTC threshold grid and remains a separate, unregistered result: it reported secant=2/6 versus pixel/growth=6/6. Do not combine those counts as a paired threshold sweep. A05 changed the estimator and used the A03 frozen grids, but remains exploratory because it ran outside a disposable container and was not preregistered.
