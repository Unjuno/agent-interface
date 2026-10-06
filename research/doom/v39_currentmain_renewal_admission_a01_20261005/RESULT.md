# V39 stale renewal admission on current main

## Disposition

**PASS — focused local regression; full V39 integration remains HOLD.** The fixed-base test reproduces the current-main failure: the old `submit_cover` rejects the test's `allow_rejection=True` path with `TypeError`, while the stale-response classifier and coverless wait are absent. The repaired source passes all four focused cases in normal and optimized Python, and the existing wait suite passes 15/15 in both modes.

The accepted response remains accepted; the exact stale-sequence rejection is recorded as no admission with no cover ID; unexpected rejections fail closed; a soft observation during coverless inference does not interrupt the planner; and a hard invalidation requests interruption.

## Commands and retained output

- `python -m unittest research.doom.test_v39_soft_stale_renewal_v1` — 4/4; `results/renewal-normal.txt`.
- `python -O -m unittest research.doom.test_v39_soft_stale_renewal_v1` — 4/4; `results/renewal-optimized.txt`.
- `python -m unittest research.doom.test_overlap_controller_v39_wait` — 15/15; `results/wait-normal.txt`.
- `python -O -m unittest research.doom.test_overlap_controller_v39_wait` — 15/15; `results/wait-optimized.txt`.
- Same focused test against `results/base_controller.py` — expected RED, exit 1; `results/base-red.txt`.
- `py_compile` passed; `results/pycompile.txt`.
- Scoped `git diff --check` passed for changed source, test, and evidence paths; `results/diff-check.txt`.
- The broader `test_map01_overlap_controller_v39` suite could not import because Pillow is absent; `results/full-controller-import.txt`. No import stubs or system dependency changes were used.

The current-main stale-renewal stack rebases cleanly from main `2f2c83c3da36566bac410b13b2ed5202c9641f1a` and changes only the V39 controller plus focused regression modules and records. It remains draft work pending non-author review.

## Scope limits

These extracted-closure tests do not execute the complete planner loop, real executor process, game, GUI, OS input, scorer, or failure-cleanup runtime. No live lane, game, model, GUI, input, container, GPU, formal allocation, task effect, reaction-time bound, recovery outcome, or MAP01 exit was measured. The full controller/import suite remains unverified. This result does not close Issue #59.
