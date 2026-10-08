# Local servo callback stalls — 2026-09-13

Candidate session_v17 rechecks original lease expiry, reply deadline and cancellation
after output delivery and before submitting a local correction. If reply submission
raises ValueError, it rechecks those conditions before retaining an unrelated error.
Original owner_v9 and mailbox release behavior is unchanged. Expired original lease
takes precedence over elapsed reply deadline, which precedes a cancellation flag;
this is state at resume time, not a reconstruction of which signal arrived first.

## Actual-app fault injection

The probe blocks output on a threading event at pointer_yield or servo_feedback,
while the owner remains independently active. It observes release before allowing
the callback to resume, then verifies no correction occurs and the pointer stays
at (631,390). Eight fresh private Inkscape sessions compare the frozen candidates:

| Condition | session_v16 | session_v17 |
|---|---|---|
| Yield output blocked past 1 s reply deadline | failed | needs_decision |
| Feedback output blocked past reply deadline | failed | needs_decision |
| Yield output blocked past 700 ms original lease | failed | expired |
| Explicit cancel while yield output blocked | failed | cancelled |

All eight independently released during blocked delivery and rejected late motion.
The old failures were `ValueError('reply no longer valid')`, not observed physical
release failures. The change improves actionable status and avoids unnecessary
tracking after the known deadline; it does not establish an input-speed gain.

Two additional session_v17 actual-app regressions preserve the earlier behavior:
unselected source reaches 24 px with saved y/size preserved; selected-source tracking
loss returns needs_decision with no saved displacement. The latter remains the
same-position selection condition, not successful shifted setup.

`audit_servo_stall.py` verifies listed source hashes, 39 exact reconstructed frames,
terminal release states and expected status mappings. All three probe processes
exited normally. Per-child process cleanup has no separate attestation. The probe
uses Event-controlled output stalls, not a real saturated network or blocked X server.
It does not test capture-before-offer stalls, every instruction-level race, or real
distractor/lost-target changes. Those claims remain open.

## Candidate use and remaining work

session_v17 is available to the Python harness. interactive_v13 remains frozen on
session_v16, so its previously published actual assistant evidence stays exact;
this report does not claim the CLI uses the new handling yet. Retained feedback
may describe a correction computed before timeout; it is not an execution receipt.
The terminal remains authoritative and exceptional stops may lack servo_outcome.

Next prioritize real distractor/target-loss coverage and stable planner-facing
feedback/schema semantics. No baseline promotion, freeze credit, token saving or
human-speed claim follows from these fault tests.
