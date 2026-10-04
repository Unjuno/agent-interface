# Issue #59 A11 — current fire-admission binding recheck

## H / T / D / C / U

**H.** The final fresh-snapshot action-admission boundary must reject health and ammo whose bindings differ by a nested bool/int alias, even when their sequence and capture timestamp match.

**T.** Run the new controller-level regression against the pre-fix A10 parent and the fixed head, then rerun the surrounding pair-monitor, action-validity, controller, wait, and source-refresh suites. Compile changed Python files and check the diff.

**D.** The controller-level regression must fail on the pre-fix parent because the mismatched current pair reaches a result instead of being rejected; after the fix, all 49 focused tests pass, compilation succeeds, and the diff check is clean.

**C.** This validates the controller's deterministic final-admission boundary with synthetic signal dictionaries. No input is issued by the test.

**U.** No game, model, GUI, OS input, or live allocation was invoked. This closes only a source-level validation gap in A10's evidence, not the live #59 gate.

## Reproduction

```sh
uv run --with 'Pillow>=10' --with 'numpy>=1.26' --with 'python-xlib>=0.33' --python 3.14 python -m unittest research.doom.test_doom_action_validity_exact_binding_v1 research.doom.test_doom_action_validity_contract_v1 research.doom.test_map01_overlap_controller_v39_pair_duplicate_consistency research.doom.test_map01_overlap_controller_v39_dual_signal research.doom.test_map01_overlap_controller_v39 research.doom.test_overlap_controller_v39_wait research.doom.test_source_refresh_v1 -v
python3 -m py_compile research/doom/doom_action_validity_contract_v1.py research/doom/map01_overlap_controller_v39.py research/doom/test_doom_action_validity_exact_binding_v1.py
git diff --check 3dbbda05eb8d5067ee2c2969615e472a0f20f562...048b10d9a91a81b026a8b097da50322160603e2c
```

`baseline-red.txt` retains the expected failure at the unfixed current-snapshot boundary. The complete post-fix output and source hashes are stored here.
