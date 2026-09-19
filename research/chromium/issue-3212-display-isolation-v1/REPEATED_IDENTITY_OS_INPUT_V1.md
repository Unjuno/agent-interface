# #3266 repeated identity plus OS input/effect v1

Decision: PASS_REPEATED_IDENTITY_OS_INPUT_SCOPED

## H/T/D/C/U

- H: Across independent p1→p2 cycles, stale p1 authority is rejected despite XID reuse, and OS input sent only to the admitted p2 window produces an exact independent effect receipt.
- T: Two fresh cycles in a pinned Debian/Chromium/Xvfb/Openbox container. Each starts p1 and p2 on fresh displays/profiles/CDP ports, retains page targets and XIDs, terminates p1, rejects the old target, installs the p2 key listener, sends x with xdotool only after p2 selection, and reads p2 title through CDP.
- D: Retain per-cycle XID reuse, old-target decision, exact input and effect readback. No target is authorized from XID alone.
- C: Every cycle must report old_target_rejected=1, p2_title=os-input-p2, XID reuse, and PASS.
- U: Two cycles and one Chromium page fixture; no cross-application coverage, no model, no user task, no product readiness, no claim over untested process/display races.

## Obstac result

- Cycle 1: p1 XID 4194307, p2 XID 4194307, old_target_rejected=1, p2_title=os-input-p2, PASS
- Cycle 2: p1 XID 4194307, p2 XID 4194307, old_target_rejected=1, p2_title=os-input-p2, PASS

Both cycles completed the stale-target negative control before sending p2 OS input.

## Scope and next gate

This strengthens #3266's pinned-fixture identity and input/effect evidence. It does not establish multi-application GUI reliability or close the broader issue. The next gate should test a negative wrong-window/old-process input control and retain the composite predicate unchanged.
