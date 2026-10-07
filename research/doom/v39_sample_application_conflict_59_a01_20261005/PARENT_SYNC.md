# Parent synchronization qualification

The original A01 matrix remains frozen against baseline commit `a1cbc360d59ca90ceb6cc5cf2ca31be5e64c0414`. The parent PR later advanced to `1ced273cc78fde3d0d9e70a147285126bfabecb0` and synchronized the upstream per-key timing tests. Its resulting source no longer contained the sample-layer rejection, so this branch was rebased and the guard/test patch reapplied on that exact current parent. Candidate commit: `44021a070f0e2729f51c358748816e8d0bcad034`.

On the rebased candidate, the focused application-consumption regression passed 1/1. The full typed-feedback module ran 30 tests: 28 passed and two errored because the sparse checkout omits `research/doom/absolute_pair_59_4d74_20261004/05-pulse/runtime/events.jsonl` and `research/doom/results/map01-v39-coast-liveness-live-01/runtime/events.jsonl`. Both command outputs and exit codes are retained beside this note. `py_compile` and `git diff --check` pass. No game, model, GUI, input, or allocation ran.

This supplemental record qualifies the patch on the latest stacked parent; it does not rewrite the frozen A01 baseline or claim live control evidence.
