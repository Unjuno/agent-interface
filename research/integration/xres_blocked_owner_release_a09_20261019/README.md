# Blocked owner I/O with independent X11 release A09

**Status:** `NOT_ESTABLISHED_REPLY_GATE_LEAK` (2026-10-19). No accepted trial.

A09 uses keycode 38 and keeps the receiver on the focused Xvfb root window. It first sends one explicit XSendEvent KeyPress solely to prove the receiver loop and event selection can record an event; this synthetic event is labeled plumbing-only and never counts as task effect. It then performs a separate direct XTEST KeyPress/KeyRelease control and requires both receiver event receipt and keymap down/up before the blocked-owner trials.

If both controls pass, the eight blocked-owner trials require task KeyPress receipt and key-down state while owner XSync is blocked, exact owner XRes client disappearance before release, independent KeyRelease receipt, and key-up readback after a 50 ms settle. The first failed trial stops the batch.

Scope is Xvfb with a responsive server and only the owner reply path blocked. This does not establish physical desktop behavior, server nonresponse, XWayland, or a real application task certificate. A01–A08 remain separate immutable records.

## Preserved first blocked-path attempt

Both controls passed: the synthetic `SendEvent` was recorded only as receiver
plumbing, and direct XTEST input produced the receiver KeyPress and keymap
state required by the preflight. The first owner-path KeyPress was also
received and key-down was observed. However, the owner returned from `XSync`
after the proxy gate was cleared, so the premise that owner replies were held
was false. The run stopped before owner retirement, XRes disconnect, or
independent release. No release result is accepted.

The first proxy implementation checked the gate before blocking in `recv` but
did not recheck it after bytes arrived. A reply could therefore be forwarded
after the gate closed. The error path also tried to remove the temporary
directory before terminating the receiver child, producing a secondary
`Directory not empty` cleanup error. Both are probe defects, not production
helper findings.

`run-result.json` records exit 1 and the raw-log hash; the exact A09 container
ID was queried after completion and was absent. A10 adds an atomic gate
check-after-receive, a withheld-reply receipt, and child-before-temp cleanup.
