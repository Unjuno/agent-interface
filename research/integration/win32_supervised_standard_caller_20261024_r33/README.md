# R33 Win32 cancellation with a proven Q-down baseline

R32 failed to establish whether the held key was down before recovery: its independent pre-cancel state readback happened after the Q-down callback was already blocked. R33 passes the injected Q-down callback, requires a separate same-generation process to read Q-down=true, then holds the first injected Q-up callback during one public cancellation. A delayed independent readback is scheduled after the recovery helper’s exact Q-up SendInput return and before the callback is released.

The fixture still requires an independently saved click and CTRL+S effect with empty text. One fixture, one dispatch, one cancel, no text operation, no retry/replay, no runtime changes, read-only registry. A successful result must distinguish Q-down baseline, exact Q-up call return, public release receipt, and actual neutral readback; SendInput return alone is not a state claim.
