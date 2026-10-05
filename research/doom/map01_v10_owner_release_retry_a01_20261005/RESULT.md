# V10 X11 release retry repair — A01

## H/T/D/C/U

- **H:** At current-main `402c7d1b5147b2a905098f082233db60a47d68db`, V39's frozen `input_owner_v10.py` dependency can lose a key-up or wheel-button release at the X server boundary. The later cleanup verifies sampled state, but does not retry inputs removed from its held map or wheel inputs it never tracks.
- **T:** Run a fake-X11 regression against the exact current-main V10 source. Suppress the first explicit key-up, then suppress a wheel button-4 release; require cleanup to retry sampled-down state and verify empty. A persistent key-release suppression must remain explicitly unverified and raise. Run normal and `-O` Python.
- **D:** Pass only if the first two suppressed releases recover to empty and the persistent suppression produces an unverified receipt plus an error.
- **C:** A mock X server cannot establish delivery behavior of a real X server, application consumption, per-client ownership, physical keyboard state, or game effect. The one-retry limit may correctly fail closed under persistent server failure.
- **U:** Live V39 input, current-main exposure, useful feedback onset, bounded recovery, and MAP01 progress remain untested; the private live-game lane remains unassigned.

## Result

The test-first baseline failed in both injected cases: a dropped explicit key-up made `release()` raise with keycode 65 still down, while a dropped wheel button-4 release remained down even though the path had not registered that button for verification. After the repair, all three regression cases pass in normal and optimized Python. The related V12 cancellation-during-key-up test also passes.

The repair samples the exact touched keycodes and buttons after the initial synchronized release, retries only those still down once, then samples again. Wheel buttons 4/5 now enter the touched-button set. Persistent key-release suppression still raises and records `verified=false` with the keycode retained.

This is a synthetic local regression repair only. It is not an Xvfb, live-game, physical-keyboard, or application-effect result and does not satisfy Issue #59's live allocation gate.

## Reproduction

From the repository root:

```sh
python -m unittest research/live_control/test_input_owner_v10_release_retry.py -v
python -O -m unittest research/live_control/test_input_owner_v10_release_retry.py -v
python -m unittest research/live_control/test_input_owner_v12_explicit_up_cancel.py -v
python -m compileall -q research/live_control/input_owner_v10.py research/live_control/test_input_owner_v10_release_retry.py
git diff --check
```

Command output is retained under `raw/`. `SOURCE_LOCK.json` binds the current-main base and changed source/test. `audit.py` independently checks the lock and required fail-closed/retry assertions without invoking X11 or changing evidence.
