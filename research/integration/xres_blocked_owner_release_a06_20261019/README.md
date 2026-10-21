# Blocked owner I/O with independent X11 release A06

**Status:** `RECEIVER_CONTROL_NOT_ESTABLISHED` (2026-10-19). Blocked-owner trials did not start.

A06 retains A05's direct focused-receiver KeyPress/KeyRelease control and blocked-path diagnostics. It fixes A05 readiness serialization by recording the focus resource ID (`Window.id`) as an integer. The input path and pass criteria are otherwise unchanged.

The eight-trial pass criteria are independent KeyPress receipt and key-down state while owner XSync is blocked, exact owner XRes client disappearance before release, independent KeyRelease receipt, and key-up readback after a 50 ms settle. The first failed trial ends the batch.

Scope is Xvfb with a responsive server and only the owner reply path blocked. This does not establish physical desktop behavior, server nonresponse, XWayland, or a real application task certificate. A01–A05 remain separate immutable records.

## Preserved preflight outcome

The receiver readiness record succeeded, but the direct observer XTEST control
timed out waiting for `trial-00-press.json`. Consequently no blocked-owner
trial ran. The captured output did not read back the keymap, window event mask,
or input focus after the timeout; it cannot distinguish an XTEST press that
failed to alter server state from a key event that was not selected/delivered
to the focused window. The XRes/release hypothesis was not tested.

`run-result.json` records exit 1 and the raw-log hash. The exact A06 container
ID was queried after completion and was absent. A07 adds these missing
readbacks at the preflight failure boundary before changing the input
construction.
