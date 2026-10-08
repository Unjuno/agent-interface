# Issue #3212 timeout/cancel terminal gates — 2026-09-20

Additive terminal-transition experiment; earlier records remain unchanged.

## H/T/D/C/U

- H: Once a receipt operation reaches an explicit timeout or cancellation terminal state before input admission, it must fail closed with no XTEST dispatch and no application/DOM effect.
- T: Three fresh Docker `--network none` allocations of `mixed-formal-2992-debian:20260920`, Xvfb, real Chromium, Xlib/XTEST, and read-only CDP DOM oracle. The fixture was reset before each terminal row; no input was sent after the terminal transition.
- D: `timeout_terminal`: admitted `0/3`, dispatch `0/3`, DOM unchanged `3/3` (`title=ReceiptFixture`, `saved=""`, `value=""`). `cancel_terminal`: admitted `0/3`, dispatch `0/3`, DOM unchanged `3/3`. Valid effect and source/restart/duplicate negative rows remained as previously measured; no `BadMatch` occurred.
- C: `PASS_CHROMIUM_TIMEOUT_CANCEL_FAIL_CLOSED_SCOPED`. This proves only the declared local terminal gate; it does not prove cancellation propagation across an external orchestrator or process crash.
- U: Run an actual orchestrator-restart allocation with persisted receipt state and independently verify cleanup/replay denial; retain any infrastructure failure as STOP/HOLD rather than inferring safety.

## Raw summary

```json
{"runs":3,"timeout_admitted":"0/3","timeout_dispatch":"0/3","timeout_dom_unchanged":"3/3","cancel_admitted":"0/3","cancel_dispatch":"0/3","cancel_dom_unchanged":"3/3","badmatch_runs":0,"formal_decision":"PASS_CHROMIUM_TIMEOUT_CANCEL_FAIL_CLOSED_SCOPED"}
```
