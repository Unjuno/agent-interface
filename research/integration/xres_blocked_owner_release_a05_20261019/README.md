# Blocked owner I/O with independent X11 release A05

**Status:** `FIXTURE_SETUP_FAILURE / NOT_ESTABLISHED` (2026-10-19). No trial ran.

A05 adds a direct observer-client XTEST KeyPress/KeyRelease control to the same focused X11 receiver before the blocked-owner trials. It verifies both event receipt and keymap state. On a blocked-path event timeout, the probe records keymap state, owner liveness/sync state, owner-to-server forwarded bytes, exact XRes client presence, and proxy errors before stopping. The A02 non-key-event receiver fix remains in place.

The blocked-owner pass criteria remain independent KeyPress receipt and key-down state while owner XSync is blocked, exact owner XRes client disappearance before release, independent KeyRelease receipt, and key-up readback after a 50 ms settle. Eight trials are requested; the first failed trial ends the batch.

Scope is Xvfb with a responsive server and only the owner reply path blocked. This does not establish physical desktop behavior, server nonresponse, XWayland, or a real application task certificate. A01–A04 remain separate immutable records.

## Preserved setup outcome

The A05 task receiver failed while writing `task-ready.json`: python-xlib's
`get_input_focus().focus` value was a `Window` object, which is not JSON
serializable. The parent timed out waiting for the readiness record. Therefore
the direct receiver control and all blocked-owner trials were not executed.
This is a fixture setup failure, not a task-effect or release result.

`run-result.json` records exit 1 and the raw-log hash. The exact A05 container
ID was queried after completion and was absent. A06 retains the receiver
control and diagnostic plan but serializes the focus resource ID as an integer.
