# #6590 T1 OrbStack allocation

This additive allocation executes the issue's visual-position model discriminator. It preserves #4752, the two prior #6590 allocations, and the geometry design screen unchanged.

## H / T / D / C / U

- **H:** With the same frozen diversified-position MLP weights and threshold, a position-random cohort sampled from the training-support neighborhood yields at least 0.20 greater positive ACCEPT than an equal-budget set of spatially blocked extrapolation centers.
- **T:** Five paired initialization/noise seeds; center-only control and five-center diversified training arms; one 144×144 9×9-patch renderer; 64 unique, patch-disjoint centers in each evaluation cohort (16 per quadrant), eight independent Gaussian-noise source images per center and class; base, position-random and spatial-block strata use the same fitted model per arm. Run candidate and an independently implemented raw-only auditor once each in separate pinned, network-none OrbStack containers. No GUI, external model, authority or retries.
- **D:** `H_PASS_SCOPED` if all frozen base-competence, false-ACCEPT, audit and support gates pass and the diversified-arm pooled position-random minus block positive-ACCEPT gap is ≥0.20. `H_FAIL_SCOPED` if the gates pass and the gap is <0.20. `HOLD_MODEL_INCOMPETENT` if base competence or false-ACCEPT bounds fail; `HOLD_AUDIT_INTEGRITY` on reconstruction mismatch; a provenance/runtime gate failure is a typed STOP. All per-seed, per-center and per-block counts remain visible.
- **C:** Larger input dimension than #4752; changed fan-in-scaled initializer; a synthetic stationary-noise renderer; the evaluation cohorts deliberately represent interpolation within versus extrapolation outside the support neighborhood. The contrast is an envelope difference, not an estimator-bias claim.
- **U:** No evidence about real GUI layouts, spatial autocorrelation in production, human/agent performance, calibration transfer, authority, safety, or product benefit. Five seeds and one renderer do not establish generality.

## Geometry

Tile 144×144, 9×9 target patch, five treatment support centers `(72,72),(51,51),(93,51),(51,93),(93,93)`, fixed negative distractor `(4,4)`. Evaluation lattice pitch 9 starts at center coordinate 10, giving at least five pixels of patch-to-edge margin. Cohorts contain 16 centers per quadrant with Chebyshev separation ≥9 from every support/distractor patch and from each other. Random centers have Euclidean nearest-support distance in `[9,27)`; block centers have distance `≥27`. Transposed NE/SW and NW/SE centers have exactly matched support distance, edge margin and distractor distance. A within-quadrant pair with differing support distance is also frozen. The exact coordinate tables are in `design.json`.

## Reproduction

See `FREEZE.json` for the allocation identity, source hashes, base/image identity, commands, seeds and all thresholds. `candidate.py` emits raw predictions and weights only; `auditor.py` independently rebuilds inputs, refits the frozen models, verifies weight hashes, and recomputes every row. `REPORT.md` and `results/` are populated only after the one-shot run.
