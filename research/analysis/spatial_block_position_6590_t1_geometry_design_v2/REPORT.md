# #6590 T1 geometry redesign screen — preformal result

## Outcome

**`PREFORMAL_GEOMETRY_SCREEN_PASS_WITH_FORMAL_ENGINE_HOLD`.** The deterministic center-grid scan found the smallest tested feasible canvas at 96×72 pixels (eligible site counts NW=12, NE=10, SW=12, SE=9). The 112×84 candidate provides more support (19/16/20/16) and is selected for the next prospective model protocol: its weakest quadrant has 16 unique centers, eight above the existing floor. The 80×60 candidate remains infeasible (7/5/4/2); 128×96 is feasible but incurs greater input dimensionality. An independent raw-only reconstruction audited all four candidates with zero errors.

This is geometry evidence only. It did not generate an image, train/evaluate a model, estimate spatial dependence, or test Issue #6590's random-minus-block effect. The selected 112×84 layout and ML protocol are not yet frozen. `docker context show` reported `orbstack`, `orbctl status` reported `Running`, but Docker API calls `docker ps` and `docker version --format ...` did not return; the latter exceeded a four-second subprocess timeout. No container was created or modified. The formal model allocation is therefore held until an authorized container runtime responds; no other/shared container was inspected or touched.

## H / T / D / C / U

- **H:** At least one larger tile can supply eight or more distinct, well-interior target centers per quadrant while keeping 9×9 evaluation patches disjoint from training-support patches and the fixed negative distractor patch.
- **T:** Enumerate a deterministic grid with pitch 9 on four canvases (80×60, 96×72, 112×84, 128×96); count centers by quadrant after frozen geometric exclusions; independently reconstruct the coordinates from the raw candidate JSON. No images and zero model fits.
- **D:** Pass this screen iff the auditor exactly reconstructs all four site tables and at least one canvas meets the eight-center floor in every quadrant. Screen outcome: PASS; minimum tested feasible tile: 96×72. Select 112×84 prospectively for headroom (minimum block count 16), not on model outcomes.
- **C:** A finite coordinate screen establishes neither statistical independence of spatial sites nor MLP competence; a larger image also changes the input dimension from 1,200 to 9,408 for the selected tile and may alter optimization behavior.
- **U:** No outcome on model accuracy, calibration, random-vs-block contrast, spatial autocorrelation, GUI grounding, safety, authority or product effect. Formal T1 needs its own frozen source, evaluator, seeds, environment identity, audit and one-shot container execution.

## Geometry

All candidates use a 9×9 target patch, 9-pixel evaluation-grid pitch, center-relative five-position training support, and a fixed negative distractor center at (4,4). Evaluation centers must be at least 9 Chebyshev pixels from each support center and distractor center. Grid centers are at least 9 pixels from tile edges, leaving a minimum five-pixel margin beyond each patch. Quadrants are split at the tile midpoint. The site coordinates are distinct and patch-disjoint; they are **not** asserted to be independent draws from a spatial process.

| Tile | NW | NE | SW | SE | Screen |
|---|---:|---:|---:|---:|---|
| 80×60 | 7 | 5 | 4 | 2 | HOLD |
| 96×72 | 12 | 10 | 12 | 9 | Feasible; least-dimension candidate |
| 112×84 | 19 | 16 | 20 | 16 | Feasible; selected with support headroom |
| 128×96 | 32 | 27 | 25 | 20 | Feasible; higher dimensional cost |

The complete coordinate tables and scan metadata are in [`results/preformal/CANDIDATE.json`](results/preformal/CANDIDATE.json); independent audit is [`results/preformal/AUDIT.json`](results/preformal/AUDIT.json). This known preformal construction output must remain labeled exploratory until a fresh prospective T1 freeze is made.

## Provenance and validation

- Candidate command: `python geometry_scan.py` from this package; host Python 3.14.5; one invocation.
- Auditor command: `python auditor.py --input results/preformal/CANDIDATE.json --output results/preformal/AUDIT.json`; separate process; one invocation; `PASS_GEOMETRY_SCREEN_AUDIT`, 4 tile candidates, errors `[]`.
- Model fits: 0. Images generated: 0. Container invocations: 0. Docker API readiness probes only: 2; no candidate/auditor containers.
- Candidate SHA-256: `f2c33436747db3edd3c6278c81395fa6fede20debc4ab695c8ec8eb57c279936`.
- Audit SHA-256: `43784e74e71ca568b44e63e8af11606a1d7a973653814002764b7404351d9428`.
- Five construction/auditor tests pass; latest-main local Analysis Index workflow-equivalent run passes at 485 retained result directories and 80 tests, using an analysis-only copy plus the frozen historical workflow source (verified 2026-10-02 09:24 UTC).

## Next gate

Freeze a new MLP successor on 112×84 only after the container engine is available. Keep the original task's target/distractor appearance and all other semantics fixed; explicitly version the changed input dimension, initializer, optimizer and learning-rate behavior. Use the same fitted weights to score equal-budget independent-source/noise samples from supported-region interpolation and preregistered disjoint spatial blocks; report unique-center and row denominators separately, worst-block positive ACCEPT, false ACCEPT, YIELD and REJECT. Geometry is no longer the immediate site-count blocker; model T1 remains unrun and the issue-level hypothesis remains unresolved.
