# Native Win32 Freedoom MAP01 producer-startup crosscheck — 2026-10-26

## Result

Three fresh native-Windows runs (R17–R19) used the standard supervised Win32
stdio MCP caller against Freedoom MAP01. Each preserved a distinct process and
target generation. The producer reported child-ready **10.203 seconds** after
the parent's `process.start` call in all three runs. Each preregistered a
30-second authority lease, completed its 344–359 ms UP action, verified neutral
release, passed the separately bound visible-effect oracle, and verified exact
process cleanup.

The frozen packet manifests contain 39 files each. This continuation
independently re-hashed all 117 entries with zero missing files or mismatches.
The measurement source `fd91b9170462358ef8e7adfd307addf6c5dcc12a` is an ancestor
of current main `9fce1ed4666b678f531a11f0ceba21dd6e7048fa`. The current runtime
diff for `owned_win32_session.py` and `win32_standard_producer.py` from that
source is empty, so the relevant timing instrumentation and child-start path
are unchanged.

## Scope

This is a descriptive three-sample result on one Windows host. The recorded
monotonic clock resolution is 15.625 ms, so identical 10.203 s values mean
repeatability at that recorded resolution, not exact equality. Parent
factory/start/identity/gate milestones were at or below about one clock tick;
R19 separately measured a 16 ms factory-request-to-return interval.

The 30-second lease runs completed, but the packets do not preserve the exact
lease-origin-to-task-completion interval. Therefore `30.000 - 10.203 = 19.797`
seconds is not an observed runtime margin or safety bound. The fixed 15-second
application settle occurred before dispatch and is not part of the action
lease. These measurements do not establish a startup distribution, blocked-I/O
release or recovery, a continuous input-release deadline, MAP01 completion,
matched model/provider efficiency, or reliability.

Private raw, preregistration, and cleanup evidence remains in local custody
packets R17–R19; all were read-only rechecked and none was replayed or edited.
No WSLc allocation or Docker operation was used.
