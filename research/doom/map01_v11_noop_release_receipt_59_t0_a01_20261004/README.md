# V11 no-op release receipt T0 A01

## H / T / D / C / U

**H:** V11 may publish `x11_release_and_sync_completed_before_return=true` for
an idempotent key-up that does not issue an X11 release request or call XSync.
This can occur when two key symbols resolve to the same X keycode: after the
first symbol releases the physical key, the second symbol's up is a no-op in
V10 while V11 still fabricates an interval receipt.

**T:** Execute the exact V10 and V11 sources pinned in `FREEZE.json` under fake
Xlib. Map W and A to keycode 77, admit both, then release W followed by A.
Count actual fake KeyRelease requests and sync calls around each returned V11
receipt.

**D:** FAIL for the unconditional receipt claim if the second receipt says
release and sync completed while the second call adds zero KeyRelease requests
and zero sync calls. Otherwise the hypothesis is not reproduced.

**C:** The aliased keysym mapping is synthetic. The result does not establish
that the live MAP01 keyboard map aliases W/A, and it does not imply that a
no-op key-up is unsafe. It shows the telemetry cannot distinguish that
no-op from an applied release under this source path.

**U:** Fake Xlib only. No real X server, keymap, physical input, game, model,
GUI, scorer, recovery, performance measurement, or live allocation. A future
receipt needs to distinguish “owner call returned” from “KeyRelease and sync
actually occurred,” and should include resolved keycode identity. The reported
interval is not evidence of physical key-up or application consumption.

## Result

The hypothesis reproduced. The first up receipt corresponded to one fake
KeyRelease request and one additional sync. The second up receipt still
reported `x11_release_and_sync_completed_before_return=true`, but added zero
KeyRelease requests and zero sync calls. Both source blobs match the frozen
current-main identities; the saved result and independent audit are retained.

## Reproduction

```powershell
python research/doom/map01_v11_noop_release_receipt_59_t0_a01_20261004/probe.py
python research/doom/map01_v11_noop_release_receipt_59_t0_a01_20261004/audit.py
```
