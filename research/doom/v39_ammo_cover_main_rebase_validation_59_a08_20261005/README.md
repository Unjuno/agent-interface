# Issue #59 A08 — post-rebase paired-cover validation

## H / T / D / C / U

**H.** The paired-ammo V39 guard, cancellation handoff, full-observation fallback, strict pair identity/time checks, source refresh, and action-validity contracts remain compatible after rebasing the PR onto current `main`.

**T.** On the frozen PR head, run the five focused suites covering paired monitoring, the V39 controller, V39 nested wait, source refresh, and immediate action validity. Compile the changed Python files and check the PR diff against the frozen base.

**D.** PASS only if all 46 tests pass, compilation succeeds, and `git diff --check` is clean.

**C.** These are synthetic observations and stubs. They do not establish producer timing, physical release, useful feedback, recovery, or game progress.

**U.** No game, model, GUI, OS input, or formal live allocation was invoked. Issue #59 remains gated on an assigned live lane and matched task-effect evidence.

## Reproduction

```sh
uv run --with 'Pillow>=10' --with 'numpy>=1.26' --with 'python-xlib>=0.33' --python 3.14 python -m unittest research.doom.test_map01_overlap_controller_v39_dual_signal research.doom.test_map01_overlap_controller_v39 research.doom.test_overlap_controller_v39_wait research.doom.test_source_refresh_v1 research.doom.test_doom_action_validity_contract_v1 -v
python3 -m py_compile research/doom/map01_overlap_controller_v39.py research/doom/test_map01_overlap_controller_v39_dual_signal.py research/doom/test_map01_overlap_controller_v39.py
git diff --check 3dbbda05eb8d5067ee2c2969615e472a0f20f562...acce7cb9ecf3ba185cae34f5892b4cc2131c62d6
```

See `RESULT.json` and `test-output.txt` for the retained result. `SHA256SUMS` binds this package and its frozen source inputs.
