# V39 cancellation release bridge A01

This opt-in successor joins the V39 bridge to the owner’s cancellation cleanup
receipt. The prior frozen bridge A01 remains unchanged.

## H/T/D/C/U

- **H:** After an admitted key is asynchronously cancelled, the owner can verify
  neutral state while the bridge keeps stale held membership and emits no
  identity-matched per-key up outcome.
- **T:** Run one V39 bridge step against the existing fake-display InputOwner
  harness. The step admits F8, sets the cancellation event, and returns. The
  bridge serializes an owner-state barrier, forwards the per-key cleanup only
  when owner, key, intent, actuation ID, original program/step, and sample
  bracket agree, then reconciles held membership only for keys covered by that
  same verified-empty owner release. No X server, GUI, game, model, or physical
  input is used.
- **D:** Pass requires one cleanup `input_release_measurement` paired with the
  original admission, a confirmed ordered physical-up sample bracket, false
  authority/application-consumption flags, empty fake physical state, and an
  empty bridge `held` set. Malformed identity, duplicate key rows, or
  unverified/incomplete cleanup must produce no receipt and retain held state.
- **C:** This tests a local software construction and adapter boundary. Fake
  Xlib provides deterministic keymap transitions; it does not establish that a
  live X server or application behaves identically. The test stubs the inherited
  V39 release backend and does not run its constructor or `session_command`.
- **U:** No real display, game, application effect, useful feedback, recovery,
  task success, live allocation, or latency benefit is measured. The cleanup
  interval is a conservative pair of keymap samples, not an exact edge time.
  Full inherited V39 startup/session composition still needs its own source and
  test closure before claiming runtime integration.

## Source lineage

The additive `input_owner_v13.py` is byte-for-byte copied from
`research/doom/map01_v39_cancel_cleanup_bracket_a01_20261005/input_owner_v13.py`
at PR #7769 head `7ff2923572adb7f9f462411936e67f65fa465799`. Its V12 dependency
sources match current-main base `2e1df9a56a0b46c1733c731bde3409c68c8750c7`.
The full source pins and hashes are in `SOURCE-PINS.json`. This package is
self-contained and does not require PR #7769 to merge.

## Reproduction

From the repository root, run:

```powershell
python -m unittest discover -s research/doom/map01_v39_cancel_release_bridge_a01_20261005 -p 'test_*.py' -v
python -m py_compile research/doom/map01_v39_cancel_release_bridge_a01_20261005/bridge.py research/doom/map01_v39_cancel_release_bridge_a01_20261005/input_owner_v13.py research/doom/map01_v39_cancel_release_bridge_a01_20261005/test_bridge.py
git diff --check
```

The wait for a cancellation cleanup record is bounded to 500 ms. The subsequent
serialized `input_state` call uses InputOwner’s existing two-second reply bound.
If no cleanup record appears within 500 ms, or the barrier does not confirm a
neutral state and unique per-key coverage, the adapter keeps pending held state
and emits no cleanup receipt. This is an offline candidate; the separately
gated live #59 lane remains untouched.
