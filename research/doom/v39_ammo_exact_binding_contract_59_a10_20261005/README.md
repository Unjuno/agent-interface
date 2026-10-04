# Issue #59 A10 — exact health/ammo binding at fire admission

## H / T / D / C / U

**H.** Fire admission must reject health and ammo signals whose nested focus/surface/geometry bindings differ, including Python `bool`/`int` aliases such as `True` and `1`.

**T.** Freeze the pre-fix contract implementation and test the paired binding boundary. Re-run the exact-binding regression and the surrounding cover/action/controller suites after the fix; compile changed Python and check the diff.

**D.** The regression must fail before the fix because the mismatched ammo binding is accepted; after the fix, all 48 focused tests pass, compilation succeeds, and the diff check is clean.

**C.** This is deterministic contract/controller evidence over synthetic signals. It does not exercise a producer, physical key events, a game, or useful task effect.

**U.** No game, model, GUI, OS input, or live allocation was invoked. The #59 live measurement gate remains open.

## Finding

Python considers `True == 1`. The action contract builder previously compared nested binding dictionaries with ordinary equality, so an ammo binding with `focus: true` could match a health binding with `focus: 1`. The final snapshot retained the health binding while the ammo binding was not independently represented there. The fix validates the exact binding shape and integer types before comparison, in both source-contract construction and current health/ammo revalidation.

## Reproduction

```sh
uv run --with 'Pillow>=10' --with 'numpy>=1.26' --with 'python-xlib>=0.33' --python 3.14 python -m unittest research.doom.test_doom_action_validity_exact_binding_v1 research.doom.test_doom_action_validity_contract_v1 research.doom.test_map01_overlap_controller_v39_pair_duplicate_consistency research.doom.test_map01_overlap_controller_v39_dual_signal research.doom.test_map01_overlap_controller_v39 research.doom.test_overlap_controller_v39_wait research.doom.test_source_refresh_v1 -v
python3 -m py_compile research/doom/doom_action_validity_contract_v1.py research/doom/map01_overlap_controller_v39.py research/doom/test_doom_action_validity_exact_binding_v1.py
git diff --check 3dbbda05eb8d5067ee2c2969615e472a0f20f562...9707310d203e04591d3648debda2733e475b53aa
```

`baseline-red.txt` retains the expected pre-fix rejection failure. `test-output.txt`, `RESULT.json`, `FREEZE.json`, and `SHA256SUMS` bind the fixed result and sources.
