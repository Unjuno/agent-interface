# Prior construction attempts (preserved, not pooled)

## A01 — STOP

The first inline diagnostic failed with `AttributeError('detail')` while trying to serialize an Xlib event. It is retained as a harness/setup STOP, not a candidate result. It was not retried under the A01 identity.

## A02 — FAIL / invalid PASS label rejected

The second inline diagnostic selected events on the window-creator connection but polled a different event connection. It recorded `MappingNotify` (type 34) and no expected KeyPress/KeyRelease on the polled connection; same/separate-query conditions had zero pending key events. Its script printed `PASS_METHOD_SCOPED` without enforcing its outcome checks. That label is invalid and rejected. No source or raw result from A02 is pooled into A03.

## A03 — separate corrected diagnostic

A03 corrected client ownership, froze `probe.py` before execution, and checked exact event type, keycode, target window, per-case fd readiness, Xlib pending-event count, keymap state, and Xvfb shutdown. See `../FREEZE.json`, `../probe.py`, `RAW.json`, and `../audit.py`.
