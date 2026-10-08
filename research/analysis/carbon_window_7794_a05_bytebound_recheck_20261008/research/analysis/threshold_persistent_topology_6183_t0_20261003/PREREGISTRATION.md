# #6183 T0 preregistration (2026-10-03)

## Status and scope

This is a new, synthetic, visual-estimand construction experiment for open
Issue #6183. It is not an application-effect, GUI, route-graph, or user-benefit
test. Application-effect output is required to remain `UNKNOWN` for every
case because this experiment has no independent application oracle.

## H / T / D / C / U

- **H:** On a frozen set of source-bound grayscale route ROIs, threshold
  persistence will correctly abstain on an antialiased one-pixel near-touch
  where a single threshold confidently reports connected, while retaining
  useful coverage on clear connected and disconnected visual predicates.
- **T:** Generate 8 deterministic 9x9 grayscale route images with endpoints at
  `(0,4)` and `(8,4)`. Compare (A) normalized pixel distance to the canonical
  connected template, (B) 4-neighbor endpoint connectivity at threshold 128,
  and (C) 4-neighbor connectivity at thresholds `[64,128,192,240]`. C reports
  PRESENT for 3-4 connected thresholds, ABSENT for 0-1, otherwise UNKNOWN.
  Images include clear connected, one-pixel gap, gray near-touch, recolor /
  brightness shift, disconnected crossing, visible occlusion, and an
  identical-pixel/different-graph pair. A separate authored visual truth
  labels each image PRESENT/ABSENT/UNKNOWN; hidden graph truth is never supplied
  to the candidate. Threshold family, ROI, fixtures, score bands, costs, and
  gates are frozen before execution. One candidate run, then one independent
  raw-only auditor run; no retries or tuning.
- **D:** `METHOD_PASS_SCOPED` only if persistent topology: (1) gets every
  determinate visual fixture correct; (2) abstains on near-touch, occlusion,
  and hidden-graph ambiguity; (3) has at least 75% coverage on determinate
  visual cases; (4) strictly beats both baselines on false confident labels;
  (5) produces identical image-only outputs for pixel-identical twins and
  never emits an application-effect certification; and (6) independent replay
  reproduces every metric with zero errors. Otherwise retain FAIL/HOLD as
  observed; no post hoc threshold changes.
- **C:** A fixed-threshold connected-component test may match or outperform
  persistence on ordinary clean images at lower cost; exact app/document graph
  queries are the preferred semantic oracle.
- **U:** Hand-authored tiny raster fixtures do not test real antialiasing,
  projection, sprite composition, zoom, temporal effects, segmentation
  transfer, or any application. Pixel fixture labels are synthetic and do not
  establish utility on an actual user task.

## Frozen scoring details

Pixel baseline uses normalized mean absolute grayscale distance to the clear
connected template: distance `<= 0.02` -> PRESENT, `>= 0.10` -> ABSENT, else
UNKNOWN. Single-threshold baseline uses threshold 128 and 4-neighbor flood fill.
The persistence method uses the four thresholds and decision rule above.
Expected visual and hidden-graph labels are isolated in `labels.json`, which
candidate code does not read. The candidate receives only `fixtures.json`,
which contains case id and pixel matrix.
Processing cost is reported as threshold-mask pixel visits; no wall-time claim.

## Runtime and reproducibility

- Source base: `fa791fe937fb24245e785d9e22928b3f4a6a42ae`.
- Branch: `research/topology-6183-t0-orbstack-20261003`.
- Additive output path: this directory.
- Runtime: new dedicated OrbStack VM `research-6183-t0-20261003`, Ubuntu
  24.04 arm64; Docker image `python:3.12-slim` pinned by resolved digest;
  `--network none`, one CPU, 512 MiB, read-only source and separate output.
- Candidate/auditor commands and hashes will be appended to `RUN.json` after
  the freeze is committed and before execution. Independent auditor is a
  separate implementation and invocation; it must not import candidate code.

## Result gate

Only the visual-method comparison can pass. Application effect remains
`UNKNOWN` for all 8 rows. An identical-image pair must have byte-identical
image-only outputs regardless of hidden graph labels. This is a finite method
test, not formal/live allocation, product readiness, or evidence of real-world
task benefit.
