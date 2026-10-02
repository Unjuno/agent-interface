# #6590 additive T1 geometry-design screen (preformal)

This package is an exploratory, deterministic layout screen only. It does not generate training/evaluation images, select model outcomes, fit a model, or consume a formal allocation. It exists to find a tile/grid candidate that can satisfy the already-stated minimum of eight independent centers per quadrant while keeping each 9×9 positive patch at least five pixels inside the image boundary and disjoint from the five training-support patches and the fixed negative distractor patch.

## H / T / D / C / U

- **H:** At least one larger tile candidate supports eight or more spatially separated, patch-disjoint evaluation centers in each quadrant.
- **T:** Enumerate only the frozen candidate dimensions and regular center grid in `geometry_scan.py`; independently reconstruct all eligible coordinates and decisions from raw geometry in `auditor.py`. This is a preformal host screen because the OrbStack Docker API is currently unresponsive; it is not the formal model experiment.
- **D:** A candidate qualifies for prospective redesign only if the independent audit reconstructs every coordinate with zero errors and all four blocks meet the eight-center floor. Otherwise HOLD and do not fit a model.
- **C:** A finite coordinate screen says nothing about MLP performance, spatial autocorrelation, calibration, or whether a larger image remains a useful task.
- **U:** The dimensions, support offsets, distractor clearance and grid are exploratory and not frozen for model training. A new protocol/image identity and one-shot container allocation remain necessary.

## Run

```sh
python -B -m unittest discover -s research/analysis/spatial_block_position_6590_t1_geometry_design_v2 -p 'test_*.py' -v
python research/analysis/spatial_block_position_6590_t1_geometry_design_v2/geometry_scan.py
```
