# Bounded native-X11 entrypoint review

Inspected exact #8094 checkout `2b0cb591c3ebcb84d1db983612613850c08fffea`, owner tests, and retained #8094/#8094-successor runtime evidence. No tests were run and no display/server was started.

## Finding: no existing native-X11 test entrypoint covers both behaviors

The smallest existing ordered two-key UP case is `research/live_control/test_input_owner_v12_key_measurement.py::KeyMeasurementTests.test_two_key_down_and_batch_up_preserve_a01_pairs` (lines 210-228). Its fixture installs synthetic `Xlib` modules and a fake display (`setUp` around lines 86-128); it does not connect to `DISPLAY`. The cleanup-first/watchdog cases are in `research/live_control/test_input_owner_v12_cleanup_measurement.py`, especially `test_cancel_before_explicit_up_retains_both_identities` (65-75) and the late-batch cause/no-I/O tests (134-149). That suite reuses the same synthetic-Xlib fixture. Both are standard-library `unittest` entrypoints; from the repository root their commands are:

```sh
PYTHONPATH=research/live_control:research/doom python3 -B -m unittest test_input_owner_v12_key_measurement.KeyMeasurementTests.test_two_key_down_and_batch_up_preserve_a01_pairs -v
PYTHONPATH=research/live_control:research/doom python3 -B -m unittest test_input_owner_v12_cleanup_measurement.CleanupMeasurementTests.test_cancel_before_explicit_up_retains_both_identities test_input_owner_v12_cleanup_measurement.CleanupMeasurementTests.test_late_batch_preserves_cancelled_cause_without_io -v
```

These commands match the retained invocation's `PYTHONPATH` layout (the archived execution used `source/research/live_control:source/research/doom`) and test the owner thread and measurement logic with fake Xlib, not native X11. The current checkout contains no `Xvfb`/`xvfb-run` launcher or native-display fixture. `input_owner_v12.py` imports Python-Xlib and XTEST and connects through `display.Display(self.display_name)` (lines 10-13, 17-19, 79-97); a native validation would additionally need an isolated X server that supports XTEST, Python-Xlib, and a focused/viewable test window satisfying the real lease focus/surface checks. The existing fake tests do not provide that environment.

## Existing execution evidence; avoid duplicate runs

- The retained #8094 full-05/full-06 runs exercise ordered batch UP in the actual V39 controller/child Session composition, but the external X/game/capture/HUD/model seams are synthetic. They are not native-X11 evidence.
- `research/doom/v15_cleanup_first_59_e0cc_20261005/full02` and `full03` exercise cleanup-first cancellation/UNKNOWN through real V39 and a real child Session process. The retained `fake_environment.py.txt` replaces Xlib modules and supplies `Display(":synthetic-e0cc")`; the Session returns a synthetic window listing and focus context (lines 120-145). These are composition evidence, not native-X11 evidence.
- Existing unit and full-child results already cover both ordered batch release and cleanup-first handback at their stated synthetic boundaries. Replaying them would not add native-X coverage.

For any separately authorized CPU-only Xvfb validation, use a fresh, private Xvfb display with XTEST enabled, a unique run/output directory outside retained evidence, and a small test client window. The current scripts are not native-ready as-is because their test setup deliberately patches `sys.modules["Xlib"]`; a native entrypoint would need a separate test module/process so those replacements cannot leak in. Do not use the unassigned #59 game/model lane or reuse the retained `full02/full03` directories.

## One-key Xvfb overlap and boundary

The parent identified existing PR #8005 as a real-Xvfb one-key `up_batch` case on #7974. It overlaps the single-key release transport/XTEST path, so that case should not be repeated. It does not cover the measured V15 owner, ordered multi-key batch, or cleanup-first watchdog-to-late-UP race. I could not resolve an #8005 ref/object in this checkout to independently inspect its exact command or output path. A nearby retained Xvfb A02 package at `research/doom/map01_v39_xvfb_per_key_release_identity_a02_20261005` is not a substitute: its retained result is STOP during focus setup, before `InputOwner` construction or any event.

The existing in-tree measured V15 full composition is intentionally synthetic, as shown by `v15_cleanup_first.../full02/fake_environment.py.txt:100-145` (it replaces Xlib and provides `DISPLAY=:synthetic-e0cc`). The retained execution inventory gives the reusable synthetic command form and isolation convention: `execution.json` specifies `E0CC_TEST_CLEANUP_FIRST=1 python3 -B probe_controller.py <fresh-directory> <scenario>` and each run gets a new output directory. That is not a native-X11 command.

A new native validation therefore needs a separate minimal unittest/driver; no existing native entrypoint can be invoked unchanged. Keep it limited to Xvfb/XTEST and the actual owner, not V39/game/model. Preserve `full-05/full-06` and `full02/full03`; write stdout/stderr, environment/package inventory, timeline, and audit output under a new uniquely named directory, never over retained runs. The existing synthetic owner commands emit JSON to stdout and need no filesystem outputs; use `-B` plus explicit log paths for any rerun. Do not infer that Xvfb/Python-Xlib is currently installed from the retained source; the run environment would need to establish and pin those dependencies before execution.
