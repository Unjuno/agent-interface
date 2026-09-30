# Issue #2447 — focus-loss probe STOP series (2447011–2447016)

All six were fresh construction allocations attempted in the pinned Docker Desktop Linux/amd64 image. **None injected the intended post-observation focus-loss fault; there is no evidence for or against InputOwner focus-guard behavior.** Formal rows=0; same-allocation retries=0.

| Allocation | Stop |
|---|---|
| 2447011 | X11 BadMatch focusing a newly created synthetic window; root-focus sentinel after failure. |
| 2447012 | PyXlib set_input_focus argument ordering error; API rejected Window object as revert mode. |
| 2447013 | xterm failed to appear in private session's wmctrl list within 5s. |
| 2447014 | xmessage failed to appear in wmctrl within 5s with geometry set. |
| 2447015 | Same xmessage readiness timeout after removing geometry and waiting 10s. |
| 2447016 | Same 10s timeout using gui_suite.Session directly. |

A separate Docker diagnostic found xmessage alive but initially IsUnmapped and absent from wmctrl; a later timing sample of the direct session showed it after about one second. This suggests a session/window-manager readiness race, not an InputOwner failure. No observation or key admission occurred in 2447013–2447016.

## H/T/D/C/U

- **H:** Focus change between observation and key-down should make InputOwner reject admission without input.
- **T:** Intended private X11 dialog, fresh image/lease, focus transfer to PointerRoot, single Right key-down.
- **D:** Require changed focus, explicit refusal, no input_admission/keycode, verified empty release. All six stopped before those checks.
- **C:** Same pinned Docker image/source bundle, isolated Xvfb/Openbox; network disabled.
- **U:** No game action, recovery, task effect, or result about the focus guard. A different harness/window-readiness method or another Issue hypothesis is needed before spending another allocation.

The six frozen snapshots and per-allocation STOP notes are in [the source/evidence bundle](raw-evidence.zip). It contains no GUI frame files because no allocation reached its observation stage.