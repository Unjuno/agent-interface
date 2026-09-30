# Local X11 activation contrast — 2026-09-28

Status: bounded synthetic construction; no implementation change and no product-level conclusion.

## Question and scope

After the 2026-09-27 #2907 public persistent-MCP task reported that `focus(inkscape)` returned a Calc screen while target metadata named Inkscape, does EWMH activation yield an observable active-window distinction from direct X input focus in a minimal private X11 fixture?

This is only a mechanism probe. It does not replay the public MCP task, launch Calc/Inkscape, capture/compare screen pixels, or satisfy #2907's mixed-app controller acceptance. It does not modify the existing fixture result or its preserved PASS/FAIL/STOP history.

## Frozen environment and protocol

- Docker context: `desktop-linux`; image: `agent-interface-desktop-integration:local-01`
- Image ID: `sha256:44634c6599b9713b382da9937db38d409c9e66bcbce95aaf2bfeae7793c11385`
- OS/architecture: Linux/amd64; run with `--network none --read-only`, a 16 MiB `/tmp` tmpfs, no host mounts.
- Private X server: Xvfb `:92`, 800x600x24; window manager: Openbox.
- Two harmless `xmessage` windows were created with fixed names/geometries: calc-probe 320x180 and inkscape-probe 320x180. No keyboard or pointer input was emitted.
- Contrast: `wmctrl -ia calc`, `xdotool windowfocus inkscape`, `wmctrl -ia calc`, then `wmctrl -ia inkscape`. After each transition, the active XID was independently polled with `xdotool getactivewindow`.
- Target metadata/visibility was independently queried using `xprop` and `xwininfo`.

## Observed output

- Two distinct window XIDs were enumerated: Calc probe `0x00400020`, Inkscape probe `0x00600020`.
- Calc activation: active XID `4194336` (Calc probe).
- Direct input-focus to Inkscape: active XID `6291488` (Inkscape probe).
- Reactivate Calc: active XID `4194336`.
- EWMH activate Inkscape: active XID `6291488`.
- Final target metadata: title `inks cape-probe` (actual WM_NAME `inkscape-probe`), class `inkscape-probe/Xmessage`; `Map State: IsViewable`; geometry 320x180.
- Process exit: 0. Network/model/input counters: 0/0/0.

## Disposition

`NULL_NOT_REPRODUCED_IN_SYNTHETIC_FIXTURE`: both direct focus and EWMH activation selected the requested active XID in this Openbox/Xvfb setup. This does not establish that either receipt proves visible application pixels, nor explain the prior real-app foreground mismatch. The fixture used synthetic xmessage windows; it did not retain a screenshot or independently compare pixels. The activation command already appears in the existing mixed-app fixture, so this result is not evidence for changing defaults or adding another activation mechanism.

## Next integration-relevant check

Keep the #2907 real-app mismatch and its unmet-task evidence authoritative. Any successor should use the same public persistent MCP/controller boundary and retain a fresh screenshot/frame digest plus active-window identity immediately after focus/activation, then have an independent observer determine whether the intended app is actually visible. Do not treat matching XID/title/class alone as a visual/task pass. No new allocation is reserved here.
