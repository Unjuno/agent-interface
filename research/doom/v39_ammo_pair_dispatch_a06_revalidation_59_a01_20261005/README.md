# Independent A06 dispatch and duplicate-epoch revalidation

This record is pinned to PR #7717 head `6cd1d2d8e0d5753819f2608941496e916dfc994c` and controller blob `d4f91d3102ef8124fdfbbd6374a3015c4e079a89`.

## H/T/D/C/U

- **H:** The updated pair monitor dispatches ordinary full observations, treats a zero-ammo pair as invalid, does not process a matching typed/full duplicate twice in either order, and fails closed on reader errors and same-epoch pair disagreement.
- **T:** Intended freeze was all 18 methods in `test_map01_overlap_controller_v39_dual_signal.py` on the exact head in offline WSLc. **That frozen command was not run.** A broader sparse checkout stalled while fetching historical blobs. Before a full suite was executed, one custom AST harness ran the exact production nested `wait()` plus pair-monitor definitions through the five cases below.
- **D:** Full-only zero ammo invalidated; typed→full and full→typed duplicates each retained exactly one soft event; a reader error invalidated as `signal_pair_source_unavailable`; a same-epoch mismatch invalidated as `signal_pair_duplicate_epoch_mismatch`.
- **C:** `PASS_A06_CURRENT_HEAD_DISPATCH_AND_DEDUP_BOUNDARY` for these five synthetic source-extracted cases. This is not an 18-test or full-suite pass.
- **U:** Does not establish whole-PR compatibility on latest main, live event ordering/frequency, game behavior, cancellation, physical key-up, useful feedback, bounded recovery, or MAP01 progress.

## Protocol deviation and execution

`FREEZE.json` was written before this run and specifies the 18-test suite. The actual command instead ran `current_head_probe.py` once, so `RESULT.json` labels `protocol_conformance` as `DEVIATED_FROM_FROZEN_T`, records zero frozen-suite executions, and limits the conclusion to the AST probe. The candidate output is preserved; it was not rerun.

The custom run used WSLc, offline, read-only mount, requested one CPU and 1 GiB, cached image `post-guard-game-59-4d74:20261004` (local image ID prefix `94014a0f7757`). WSLc warned that swap/cgroup memory enforcement was unavailable; no memory-enforcement claim is made. No GPU was allocated.
