# A02 STOP: focused X11 client event witness

The one frozen candidate invocation exited 1 after `wait_key_event` timed out while waiting for the focused client to receive a matching `KeyPress` for keycode 25. The independent auditor was not run. Candidate stdout, stderr, and exit status are retained beside this record.

The harness discards key events that do not match the expected type, keycode, and window before raising the timeout. It therefore does not show whether the server delivered no event or delivered an event whose identity did not match the predicate. The candidate did not serialize its partially collected state before raising, so no raw keymap or owner receipt is available for this invocation.

No candidate retry was performed. This STOP does not support a claim that InputOwner failed to send, that the client received a wrong event, or that application event delivery is impossible. It identifies an instrumentation gap for any future, separately frozen diagnostic.

Environment: isolated OrbStack Ubuntu 24.04 arm64 VM `v39-x11-client-event-effect-a02-20261004` (`01M42F4H1TA74D5P5PA9N3YVNE`); Xvfb and Python-Xlib 0.33. Source InputOwner v10 is pinned to main commit `13bab54ea6d91978247ecc1b70e5060db752367a`, Git blob `341b3c01649943ddaad5f28431a792c4889cc36e`, SHA-256 `ceae7d9983cd0ba13a35e01ce2ce7dbbf03a0397b23ddc123b0110b4d4de670b`.
