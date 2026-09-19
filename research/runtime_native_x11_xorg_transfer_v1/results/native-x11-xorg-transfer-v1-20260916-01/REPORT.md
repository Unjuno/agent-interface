# Native X11 Xorg-dummy environment transfer v1 — retained first result

**Result ID:** `native-x11-xorg-transfer-v1-20260916-01`  
**Source/plan freeze:** `21bbb02f4608a4315d6fdb1665b2a8f236f899c7`  
**Dependency native-tight source freeze:** `48030f5829690bdd3209d05974e390d88e7742a9`  
**Dependency retained head:** `3f6e46556e44983d39e306a58ca80c688e7b2af5`

## Disposition

**ENVIRONMENT_TRANSFER_PASS_1MS / RETAIN_XORG_DUMMY_TRANSFER / DO_NOT_GENERALIZE**.

The fixed formal order `1,12 ms` completed once per arm on fresh X.Org Server 21.1.16 dummy-driver displays with Openbox, isolated LibreOffice Calc profiles and fresh XLSX outputs. Both arms used the exact frozen compiled Go+cgo/X11/XTest tight-loop dependency from PR #145.

| pacing | exact corpus | controls | median native char-start | edit interval |
| ---: | ---: | :---: | ---: | ---: |
| 1 ms | **16/16** | PASS | **1.176324 ms** | **207.955 ms** |
| 12 ms | **16/16** | PASS | **12.308731 ms** | **1822.327 ms** |

On this fixed Xorg-dummy Calc workload, 1 ms is **1614.372 ms / 88.59% shorter** than 12 ms at equal durable correctness. This is a fixture-local edit interval, not product or end-to-end agent latency.

## Controls / evidence closure

- preformal source closure: 8/8 local source files matched GitHub blobs after the corrected freeze;
- the earlier `cea2b231...` freeze had one detected local-vs-GitHub `run_arm.py` mismatch, so **no formal arm was started**; the validated development byte sequence was then frozen at `21bbb02f...` and rechecked 8/8;
- formal arm reruns: **0**;
- both arms refused stale text as `STALE_OBSERVATION` with zero injected events;
- both arms ended with verified empty terminal release, including the bounded save-confirm step;
- controller/scorer/internal outer exit receipts are 0 for both arms;
- both XLSX files independently score 16/16 exact and all 11 ZIP members pass CRC readback;
- server receipts identify `The X.Org Foundation`, release `12101016`, X.Org Server 21.1.16, XTEST present, 1280x800x24;
- exact controller SHA-256: `3a1a5207bc44aa67a5bd695a6307fc586f28ee791dc7544c601a018e65e7e04a`;
- the surrounding container UI appended the known `TERM environment variable not set` after child completion; no arm was rerun and decisions use retained child receipts.

## Interpretation

This closes one implementation/environment confound: the 1 ms candidate remains exact when the compiled native tight-loop moves from the earlier private Xvfb setup to a separately launched Xorg dummy-driver server. It does **not** prove a universal pacing constant; both environments still share Linux/X11/XTest, the same host/container, Openbox and LibreOffice.

## H/T/D/C/U

**H:** 1 ms strict-ASCII pacing remains sufficient under a distinct X server setup, while 12 ms remains a correctness-positive but slower control.  
**T:** source-frozen two-arm real Calc transfer, fresh Xorg/Openbox/profile/XLSX per arm, independent post-execution workbook scorer, no model/provider/network calls.  
**D:** ENVIRONMENT_TRANSFER_PASS because both arms are exact and all stale/release gates pass.  
**C:** Xorg-dummy and Xvfb share much of the X.Org/XTEST stack; host load, real GPU/display, WSLg/Xwayland, locale and IME may change the safe pacing.  
**U:** same machine/container, strict lowercase ASCII, one Calc session per arm; no 0 ms Xorg-dummy arm, no WSLg/Wayland/Windows/macOS/provider-token evidence.

## Successor

Do not add another same-host X server mode unless it changes the delivery stack materially. The next useful discriminator is a real/alternate host display path such as WSLg/Xwayland or a native non-X11 backend. If that is unavailable, keep 1 ms as a measured X11 backend candidate rather than a common semantic default.
