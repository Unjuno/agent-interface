# V39 receipt-linked per-key measurement, mainline compatibility

## H / T / D / C / U

- **H:** Per-key admission receipts can be attached to explicit release transitions while preserving the current `InputTransitionOwner v3` keycode marker and verified cancellation-cleanup join.
- **T:** Reproduce the retained `up_batch` cancellation race against current `main` and PR #8108 source with a deterministic fake owner; add matching-keycode and wrong-keycode controls; then join admission receipts to release bounds with the candidate analyzer.
- **D:** PASS only when the current source retains keycode identity for fail-closed cancellation cleanup, reports a matching admission receipt on ordinary per-key releases, rejects a cleanup for a different keycode, and the analyzer rejects mismatched/reused/malformed edges.
- **C:** Fake-owner and synthetic-event construction evidence. It does not measure X11 timing or application/game effect.
- **U:** No GUI, game, model call, physical input, live allocation, useful-feedback onset, or MAP01 progress was tested.

## Result

The PR #8108 owner source, exercised with the current-main fake-owner fixture, raises `ValueError` when cancellation cleanup wins a queued `up_batch`, even when the cleanup record verifies release of the admitted key. Current `main` returns a `cancelled_cleanup_join` transition for that exact keycode and rejects the same cleanup record when it names a different keycode.

The mainline adaptation stores the admission receipt in marker slot 6 while preserving the existing keycode in slot 5. The ordinary release transition carries the matching admission receipt and validity flag. The cancellation path preserves its keycode join and reports the admission receipt without claiming an ordinary release or granting input authority. Regression tests fail against the old PR owner source and pass against this adaptation.

The existing release-batch owner-race integration test now asserts that the admission event and cancellation release event retain the same key, owner, and intent receipt through the real V12/V3/V4/backend composition. It passes on this adaptation and fails against PR #8108's old V3 source, which leaks the cancellation `ValueError` through the backend.

The analyzer uses `key` for keyboard releases and `button` for pointer-button releases, matching the runtime event shape. The pointer positive-control is schema-only: current V39 owner code does not provide a verified pointer-button release transition, so no live pointer measurement claim is made.

## Validation

Python 3.11.9, base `f185a9059d485a4f8d5a65e9e7f6782897f67eae`.

- Owner V3/V4, V15, V39 controller, owner-to-analyzer, and release-batch backend race suites: 45 tests passed in normal and optimized mode.
- Receipt-linked analyzer suite: 4 tests passed in normal and optimized mode.
- Owner-to-analyzer composition suite: 1 test passed in normal and optimized mode; the V3 transition receipt is consumed by the candidate analyzer and yields the expected per-key censored interval.
- Python compilation and `git diff --check`: passed.
- Deterministic cancellation comparison: matching keycode is preserved as a non-ordinary verified cleanup on current `main`; the mismatched keycode control is rejected. The PR #8108 source propagates the cancellation `ValueError` for the matching case.

The test suites are construction evidence only. Live control remains unverified.

## Reproduction

From the repository root:

```powershell
python -m unittest -v research.live_control.test_input_transition_owner_v3 research.live_control.test_input_transition_owner_v4 research.doom.test_session_map01_v15 research.doom.test_map01_overlap_controller_v39
python -O -m unittest -q research.live_control.test_input_transition_owner_v3 research.live_control.test_input_transition_owner_v4 research.doom.test_session_map01_v15 research.doom.test_map01_overlap_controller_v39
python -m unittest -v research.doom.test_map01_direct_retained_input_owner_integration_v1
python -O -m unittest -q research.doom.test_map01_direct_retained_input_owner_integration_v1
python -m unittest -v research.doom.test_release_batch_owner_race_composition
python -O -m unittest -q research.doom.test_release_batch_owner_race_composition
```

From `research/doom`:

```powershell
python -m unittest -v test_analyze_map01_direct_retained_input_v2
python -O -m unittest -q test_analyze_map01_direct_retained_input_v2
```
