# Issue #4136 plan / frozen H-T-D-C-U

Formal rows: **0/20** at this source publication.

- H: a foreign active X11 pointer grab can divert an XTEST click even while XQueryPointer leaf remains Entry A. A pre-click GrabPointer probe can detect an already-active grab but not a grab that begins after the probe.
- T: HIT_ONLY vs HIT_GRAB_PROBE; CLEAR / GRAB_BEFORE_CHECK / GRAB_AFTER_CHECK; three repetitions, balanced arm order = 18 cases, plus two NO_TASK_INPUT controls. Fresh app+grabber processes per case on one private Xvfb. Fixed text is digit 7 after post-click focus=A only.
- D: exact 20-case table and PASS_POINTER_GRAB_BOUNDARY_SCOPED gates are those in Issue #4136. No result-dependent threshold exists.
- C: cooperative X11 clients, owner_events=False grab, server-logical input only, diagnostic probe briefly grabs in eligible cases.
- U: passive/keyboard grabs, owner identity, arbitrary apps/toolkits, model/task utility, production adoption and natural incidence remain open.

Excluded construction: two cases only, never pooled: HIT_ONLY/CLEAR -> A=7; HIT_GRAB_PROBE/GRAB_BEFORE_CHECK -> leaf=A, probe AlreadyGrabbed, zero click/text/foreign effect.

Formal rule: one orchestration, no same-ID retry/replacement/pooling/tuning. Missing process/raw/cleanup evidence is STOP/HOLD.
