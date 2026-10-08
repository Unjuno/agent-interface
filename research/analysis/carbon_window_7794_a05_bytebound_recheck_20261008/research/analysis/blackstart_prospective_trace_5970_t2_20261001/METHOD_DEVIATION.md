# T2c method deviation and transfer boundary

The frozen archive and original #4135 `app.py` / `observer.py` source hashes were verified. However, the T2c runner launched `instrumented_app.py` and `instrumented_observer.py`, which are purpose-built, test-specific copies modeled on the archived Tk Entry and Xlib event-loop shape. It did **not** mechanically patch, derive, or execute the exact archived source files. The source check therefore establishes provenance of the reference fixture, not provenance of executable code for the live T2c trace.

This deviation narrows the result further: the missing observer `KeyPress` is a valid result for the executed isolated replica and its selected window-event subscription, but it cannot be attributed to the original #4135 implementation. The candidate still correctly held because its own observer stream had no paired record. Do not cite T2c as evidence that #4135's original observer drops XTest events.

Any successor intended to test transfer to #4135 must freeze a mechanical source transformation (or exact diff), prove the transformed bytes derive from the archive hashes, and run that transformed code under a fresh isolated display. Keep the current three attempt outputs immutable; no original allocation retry is authorized by this result.
