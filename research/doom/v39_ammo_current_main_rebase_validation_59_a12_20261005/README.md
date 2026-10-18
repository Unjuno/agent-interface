# Issue #59 A12 — paired-ammo suite after current-main rebase

## H / T / D / C / U

**H.** The paired observation dedupe fix, exact fire-binding checks, V39 cancellation boundary, action-validity contract, and source-refresh behavior remain compatible after rebasing onto the latest `main`.

**T.** Freeze the exact post-rebase head and run the seven focused suites covering exact source/current bindings, action validity, duplicate projection consistency, paired cover, V39 controller, nested wait, and source refresh. Compile the changed Python files and check the diff against the frozen main.

**D.** PASS only if all 49 tests pass, compilation succeeds, and `git diff --check` is clean.

**C.** These are synthetic signals and stubs. They do not measure producer timing, physical release, useful feedback, bounded live recovery, or task effect.

**U.** No game, model, GUI, OS input, or formal live allocation was invoked. Issue #59 remains open for matched live evidence.

## Reproduction

```sh
uv run --with 'Pillow>=10' --with 'numpy>=1.26' --with 'python-xlib>=0.33' --python 3.14 python -m unittest research.doom.test_doom_action_validity_exact_binding_v1 research.doom.test_doom_action_validity_contract_v1 research.doom.test_map01_overlap_controller_v39_pair_duplicate_consistency research.doom.test_map01_overlap_controller_v39_dual_signal research.doom.test_map01_overlap_controller_v39 research.doom.test_overlap_controller_v39_wait research.doom.test_source_refresh_v1 -v
python3 -m py_compile research/doom/doom_action_validity_contract_v1.py research/doom/map01_overlap_controller_v39.py research/doom/test_doom_action_validity_exact_binding_v1.py
git diff --check 144dbb1114e508d5a6ffeca00d13aae89905a157...140e5afb5cb1917548caca2a92246e77268a2c56
```

See `FREEZE.json`, `RESULT.json`, `test-output.txt`, and `SHA256SUMS` for exact source and result identities.
