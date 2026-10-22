# Executor V3 Hard-Kill Xvfb A01

## Scope and pre-registration

This one-shot arm tested whether an X server clears key state when the process containing the current-main Executor V3 and InputOwner V4/V12 is forcibly killed during a held key.

- **H:** Forced death bypasses `Executor._run`'s `finally` release and owner shutdown; Xvfb may retain the down state.
- **T:** A dedicated Xvfb, current-main Executor V3 worker, current InputOwner V4/V12, one actual `a` hold, independent KeyPress/keymap confirmation, SIGKILL, and keymap/event observation around the registered one-second boundary.
- **D:** PASS only if actual KeyRelease and keymap-up are observed within one second; FAIL_STUCK_KEY if the worker is confirmed dead and keymap remains down spanning the deadline; STOP for missing preconditions or harness/cleanup errors.
- **C/U:** One isolated Xvfb sample; no production supervisor, separate persistent owner, game, physical input, or live allocation.

## Result

**FAIL_STUCK_KEY (independent raw audit).** The worker held a key, was killed with return code -9, and the X server continued reporting that key down. The independent auditor recomputed absolute timestamps from the raw log: all 33 keymap samples in the first second were down, including a sample at 998 ms after SIGKILL; the first sample after the one-second deadline was also down. Xvfb exited cleanly after evidence capture.

The raw event stream also contains repeated KeyRelease/KeyPress pairs after the kill, but none coincides with an up keymap sample. These events therefore do not demonstrate release; the keymap remains the deciding observation.

The candidate's raw field `key_up_within_1s` was calculated over a one-second polling interval that began only after waiting for a KeyRelease, so that field does not represent the registered absolute deadline. The raw-only auditor does not rely on that field; it verifies timestamps and reports 33 all-down samples through the deadline. The frozen candidate was not rerun or modified.

This demonstrates that process death alone did not release a held Xvfb key in this fixture. It does not test a separate persistent owner/supervisor or production controller recovery. See `AUDITOR/audit.json`, `results/A01/RAW.json`, and `FREEZE.json`.
