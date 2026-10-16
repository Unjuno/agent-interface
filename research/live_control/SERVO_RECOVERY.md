# Actual assistant recovery after false visual goal — 2026-09-13

One known-fixture assistant episode completed after a false local visual goal.
This demonstrates a recovery path under controlled environment restoration, not
an automatic semantic verifier or a correction of the tracker's identity flaw.

`interactive_recovery.py` uses a research-only `recovery_fixture.py` wrapper around
session21. The first servo's feedback contains the same opaque child-window
replacement from the prior fault test. The environment removes it after that servo
returns, with an explicit environment event. Later programs receive normal pixels.
This is controlled fault injection; the assistant did not identify/remove an unknown
real overlay. The wrapper is not an application API for control or a runtime feature.

The assistant viewed initial image 001 and issued the 24 px target. It inspected
image 002 after local_goal_reached: the apparent object was displaced, but Inkscape's
X toolbar still showed 50 and status indicated zero movement. Those GUI cues were
inconsistent with the intended effect. The assistant knew the test scenario, so
this is not blind anomaly detection evidence.

It requested Escape/settle under a new program to clear selection and get fresh
feedback. The first inspected intermediate image still showed selection handles;
it then resolved the latest observation's reused PNG path and viewed image 007.
The actual object remained at its original location. Recovery used source sequence
9 and a new explicit lease. No released hold or obsolete ticket was resumed.

After the recovery servo, the assistant viewed image 011: toolbar X=70.339 and the
object displacement agreed. A separate GUI save/settle program ran before independent
XML scoring. The final displacement is 23.99999876 screen px at 118% zoom, with
y=50, width=40, height=30 and no transform preserved. The legacy score passes.
No saved-file oracle was read to choose the recovery action.

## Timing and cost endpoints

All durations below use the runtime perf_counter_ns clock; they include different
scopes and must not be conflated:

| Endpoint | Duration |
|---|---|
| Initial servo accepted → terminal | 825 ms |
| Reobserve accepted → terminal | 546 ms |
| Recovery servo accepted → terminal | 835 ms |
| Save accepted → terminal | 424 ms |
| False terminal → recovery accepted | 59.717 s |
| First servo accepted → independent score known | 97.400 s |

The episode used four accepted programs and five explicit clock commands. These
are recorded command counts, not all model/tool calls. Image viewing, log lookup,
reasoning and tool orchestration contribute to the long gaps; their isolated
contributions were not measured. Initial planning/launch precede the 97.4-second
interval. Final scoring waits for the assistant's finish command, so this endpoint
also includes orchestration delay. No token accounting, latency distribution or
human-speed claim is available from this one episode.

`audit_servo_recovery.py` checks 16 exact frame reconstructions, listed source hashes,
program ordering, release verification, new recovery source/lease and saved scoring.
The first false-goal diagnosis is the assistant's known-fixture GUI judgment, not
an assertion that the audit proves semantic mismatch from pixels. The process exited
normally; per-child cleanup has no independent attestation.

## Next decision

The runtime can execute a recovery once the planner notices the inconsistency, but
the full path remains expensive. Improve model-visible current-image addressing and
endpoint telemetry, and evaluate whether explicit effect evidence can avoid redundant
inspection/clock exchanges without changing authority validity. Repeating more
subsecond motor microbenchmarks will not explain this minute-long recovery gap.
The patch identity flaw remains open; environment-restored success is not proof of
recovery from persistent occlusion or a wrong-direction move. No runtime promotion.
