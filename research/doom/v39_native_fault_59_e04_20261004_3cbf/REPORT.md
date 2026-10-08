# E04 first outcome — STOP_RESULT_RETENTION_X11_CLOSE

Prospective freeze: 96b72496f5e93937b52d1fd35513cc15f1da0426.
Independent prelaunch review Curie READY for one-shot launch only.
Prospective Issue59 comment5973856518; no peer source/allocation was used.

## Formal execution

Own container e04-native-fault-formal-3cbf-20261004:
2026-10-03T21:58:15.36541315Z to21:58:19.838367424Z, exit1/noOOM.
Actual sampled cgroups CPU100000/100000, memory1073741824, swap0,pids128,
UID501. Runtime records1917 source pins/10 execution pins; digest-pinned
private image560af28c… and historical source96d39ca… match the freeze.

First original_fault cell began. Retained intact native stdout has23 rows:
ready1, accepted1, keys_held1, cancel_requested1, input_released1, terminal1,
full observations5, typed observations5, and clock/control records.
Native raw reports accepted token7fd1a37511b846af9830d621df785688,
Right admission, matched cancel, same-token cancelled early owner release
followed by cancelled terminal with verified empty keys/buttons.
Clock probe19→90 tic in2.0350513969897293 seconds without advance calls.
Post-control score0kills/0deaths/map_exitfalse, not gameplay success.

After the child session closed its owned Xvfb, observer.close() in runner
finally raised Xlib.error.ConnectionClosedError. RESULT.json and SUMMARY.json
were never written; remaining candidate_fault/candidate_healthy cells0.
Reader outcome, injected fault timestamp, independent full held/neutral
snapshots, thread retirement and child exit are NOT recoverable from a missing
RESULT. Native event reports alone cannot fill those gates. This is an exposed
native action trace with incomplete research result retention, NOT a scientific
fault/cancel PASS. No original parser-fault result is asserted from timing alone.

Distinct official frozen auditor e04-native-fault-auditor-3cbf-20261004:
2026-10-03T21:59:24.767764356Z to21:59:24.93772329Z, exit1/noOOM,
FileNotFoundError /native/record/SUMMARY.json. AUDIT.json absent.
Formal native1/official auditor1/retries0/model0; both allocations consumed.
Neither is repaired or rerun.

## Custody and scope

Native output25 files equals distinct terminal docker-cp export25 files by
exact relative file set and bytes. Both are retained; original execution pins
still match all10 inputs. Raw terminal/log receipts preserve both failures.
Separate verify_retention.py verifies failed disposition/custody only; it does
not execute the frozen official auditor or native game, and reports
scientific_pass=false. It cannot recreate lost RESULT observations.

The new entry fix demonstrably crosses the E03 import-startup STOP and reaches
an actual native submit/cancel path, but does not validate E02 candidate behavior
in native sessions, broad physical safety, model control, task-effect, efficiency,
current-main production qualification or the full roadmap.

## Next experimental boundary

The consumed runner remains immutable. A future separately frozen successor
must preserve result writing despite display-close cleanup faults, test that
boundary before another allocation, and retain cleanup exceptions explicitly.
After independent review, revalidate the same unresolved Issue59 three-case
question in fresh paths/allocation; no new Issue merely for this wrapper repair.
E03 predecessor STOP and this E04 first failure remain unchanged.
