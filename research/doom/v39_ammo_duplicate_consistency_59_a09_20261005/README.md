# Issue #59 A09 — same-epoch paired projection consistency

## H / T / D / C / U

**H.** When a typed observation is followed by its ordinary observation at the same sequence and capture time, the two health/ammo projections must agree before the ordinary row is treated as a duplicate. Conflicting evidence must invalidate the active fire cover.

**T.** Freeze the pre-fix parent and current source. Run one regression against the parent, then the same regression and five surrounding focused suites against the fix. Compile changed Python and check the branch diff.

**D.** The regression must fail on the pre-fix parent because conflicting same-epoch ammo is silently accepted; after the fix, all 47 focused tests pass, compilation succeeds, and the diff check is clean.

**C.** The reader fixture provides synthetic projection values; this verifies controller behavior, not producer timing or an actual game image.

**U.** No game, model, GUI, OS input, or live allocation was invoked. This is a local source-contract correction, not live feedback, recovery, or task-effect evidence.

## Finding

Before the fix, the typed-then-ordinary shortcut accepted a matching sequence, timestamp, and binding without reading the ordinary row. That allowed conflicting health/ammo projections through when a comparable frame hash was absent. The fix extracts the ordinary pair and compares both typed signal contents and frame identity before deduplicating; disagreement fails closed.

## Reproduction

```sh
uv run --with 'Pillow>=10' --with 'numpy>=1.26' --with 'python-xlib>=0.33' --python 3.14 python -m unittest research.doom.test_map01_overlap_controller_v39_pair_duplicate_consistency research.doom.test_map01_overlap_controller_v39_dual_signal research.doom.test_map01_overlap_controller_v39 research.doom.test_overlap_controller_v39_wait research.doom.test_source_refresh_v1 research.doom.test_doom_action_validity_contract_v1 -v
python3 -m py_compile research/doom/map01_overlap_controller_v39.py research/doom/test_map01_overlap_controller_v39_pair_duplicate_consistency.py research/doom/test_map01_overlap_controller_v39_dual_signal.py research/doom/test_map01_overlap_controller_v39.py
git diff --check 3dbbda05eb8d5067ee2c2969615e472a0f20f562...ce1eb94e7419c47318a2bad0f9fe3b5f8fae63f5
```

`baseline-red.txt` is the one-test run against the unfixed parent. `test-output.txt`, `RESULT.json`, `FREEZE.json`, and `SHA256SUMS` retain the fixed result and exact source identities.
