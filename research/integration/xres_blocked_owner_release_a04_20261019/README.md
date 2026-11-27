# Blocked owner I/O with independent X11 release A04

**Status:** `NOT_ESTABLISHED` (2026-10-19). Trial 1 stopped before the task-effect gate.

A04 uses the A02 receiver fix: non-KeyPress/KeyRelease events are ignored before accessing `event.detail`. A03's PowerShell argument-splitting failure is retained separately and did not invoke the probe. The complete `/repo/.../probe.py` argument is asserted as one argv element before the WSLc launch.

The eight-trial pass criteria are independent KeyPress receipt and key-down state while owner XSync is blocked, exact owner XRes client disappearance before release, independent KeyRelease receipt, and key-up readback after a 50 ms settle. The first failed trial terminates the batch.

Scope is Xvfb with a responsive server and only the owner reply path blocked. This does not establish physical desktop behavior, server nonresponse, XWayland, or a real application task certificate. A01–A03 remain separate, immutable records.

## Preserved first trial

The probe launched with the intended single script-path argument, installed the
pinned Xvfb/python-xlib dependencies, then timed out waiting for the task
receiver's `trial-01-press.json`. No task-side KeyPress receipt was established,
so the acceptance sequence did not reach owner retirement, XRes disconnect, or
independent release. This outcome neither proves nor disproves that Xvfb
processed the queued press; the probe did not preserve a keymap readback or
receiver event trace at the timeout. Do not count this as a release pass or a
release failure.

`run-result.json` records exit 1 and the raw-log hash. The exact container ID
was queried after the run and was absent. A05 adds a direct, responsive-server
receiver control and diagnostic receipts before the blocked-owner condition;
A04's source and raw remain unchanged.
