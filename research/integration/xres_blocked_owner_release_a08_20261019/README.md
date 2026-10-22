# Blocked owner I/O with independent X11 release A08

**Status:** `RECEIVER_CONTROL_NOT_ESTABLISHED` (2026-10-19). Blocked-owner trials did not start.

A08 changes the task receiver from a child window to the Xvfb root window. It focuses the root, selects KeyPress/KeyRelease there, and retains A07's keymap/focus/event-mask diagnostics. This isolates child-window delivery from the rest of the same XTEST path; it is not an application task-success test.

After the direct XTEST control passes, the eight blocked-owner trials require the matching KeyPress and key-down state while owner XSync is blocked, exact owner XRes client disappearance before release, independent KeyRelease receipt, and key-up readback after a 50 ms settle. First failure stops the batch.

Scope is Xvfb with a responsive server and only the owner reply path blocked. This does not establish physical desktop behavior, server nonresponse, XWayland, or a real application task certificate. A01–A07 remain separate immutable records.

## Preserved preflight result

Using the Xvfb root as the focused event target did not change the outcome:
the direct observer XTEST control set keycode 250 down, but the root receiver's
key-event journal remained empty. The receiver and independent observer both
reported focus ID 1293, the receiver's KeyPress/KeyRelease mask was `3`, and the
root remained viewable. No blocked-owner trial ran; release was not tested.

`run-result.json` records exit 1 and the raw-log hash. The exact A08 container
ID was queried after completion and was absent. A09 will use an explicit
`SendEvent` only to verify that the receiver loop records an event; that event
will not count as task effect. It will then use a standard mapped keycode for a
separate direct XTEST control before any blocked-owner trials.
