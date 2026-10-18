# Blocked owner I/O with independent X11 release A07

**Status:** `RECEIVER_CONTROL_NOT_ESTABLISHED` (2026-10-19). Blocked-owner trials did not start.

A07 preserves the A06 direct XTEST receiver control. If its KeyPress receipt times out, the probe will capture input focus before/after, receiver-selected event mask and map state, target window map state, keymap state, server keycode range/mapping, and a JSONL journal of all receiver key events. This should distinguish an XTEST state change from event selection/delivery failure without starting blocked-owner trials.

If the control passes, the eight blocked-owner trials retain the same owner-block, exact-XRes-disconnect, independent-release, and settled-key-up criteria. First failure stops the batch.

Scope is Xvfb with a responsive server and only the owner reply path blocked. This does not establish physical desktop behavior, server nonresponse, XWayland, or a real application task certificate. A01–A06 remain separate immutable records.

## Preserved preflight result

The direct observer XTEST control set the keymap bit for keycode 250, but no
KeyPress event appeared in the receiver's key-event journal. At timeout, both
the receiver and the independent observer reported input focus ID 4194304,
which matched the mapped task window; the receiver reported event mask `3`
(KeyPress and KeyRelease), and the window remained viewable. Xvfb's reported
keycode range was 8–255. This separates server key-state change from
application-window event receipt: the latter was not established. No
blocked-owner trial ran and there is no release result.

The XTEST protocol defines `detail` as a physical keycode, rejects values
outside the server's min/max keycode range, and says simulated events undergo
normal propagation/grab processing. The captured 250 is within the observed
range, but this does not explain the missing receiver event. [XTEST protocol
specification](https://www.x.org/archive/X11R7.0/doc/PDF/xtest.pdf).

`run-result.json` records exit 1 and the raw-log hash. The exact A07 container
ID was queried after completion and was absent. A08 changes the receiver to
select input on the focused root window as a minimal dispatch diagnostic; it
will not be treated as an application task-success test.
