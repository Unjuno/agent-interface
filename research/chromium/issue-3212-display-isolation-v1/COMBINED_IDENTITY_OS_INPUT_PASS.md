# #3266 combined identity and p2 OS input/effect gate v1

Decision: PASS_COMBINED_IDENTITY_OS_INPUT_SCOPED

## H/T/D/C/U

- H: After p1 teardown and p2 generation admission, an old p1 CDP target is rejected even when XID is reused, and a bounded OS key event sent only to the admitted p2 X11 window produces an exact independent application receipt.
- T: Fresh Debian bookworm-slim; p1 on Xvfb :231/CDP 9341 and p2 on :232/CDP 9342; retain page targets, XIDs, WM_PIDs and process generations; close p1; reject old target; install p2 key listener; activate p2 window; send x with xdotool; read p2 title through CDP.
- D: Retain both negative and positive decisions, exact input command, XID reuse and independent title receipt. No target is admitted from XID alone.
- C: PASS requires old_target_rejected=1, p2 title=os-input-p2, p1/p2 XID/WM_PID evidence, and no setup or cleanup failure.
- U: One Chromium page fixture only; no multi-application reliability, no model, no user task, no production integration, no claim that all stale process/display races are covered.

## Obstac result

OBSTAC_COMBINED_IDENTITY_OS_INPUT PASS old_target_rejected=1 p2_title=os-input-p2

- p1: XID 4194307, WM_PID 6194, display :231, CDP 9341
- p2: XID 4194307, WM_PID 6342, display :232, CDP 9342
- old p1 CDP target: rejected
- p2 OS input: xdotool key x
- independent effect: title=os-input-p2

XID reuse was observed and did not authorize p1. The input was sent only after p2 identity selection and was confirmed by an independent CDP readback.

## Scope and next gate

This is a scoped p1/p2 identity plus one OS input/effect PASS for the pinned container fixture. It does not close #3266, establish cross-application GUI reliability, or qualify the full desktop path. The next gate must add stale old-process and negative-target controls across repeated allocations without weakening the predicate.
