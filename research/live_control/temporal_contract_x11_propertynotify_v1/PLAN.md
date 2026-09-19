# #1786 Private-X11 PropertyNotify temporal-monitor transfer

TASK: `TEMPORAL-CONTRACT-X11-PROPERTYNOTIFY-R1-20260918-001`

Parent: #1764 / PR #1783 `PASS_TEMPORAL_CONTRACT_MONITOR_COMPILATION_A3_SCOPED`.

One empirical factor only: replace the synthetic timestamp-fragment source for `A_THEN_B_WITHIN(80ms)` with a private X11 `PropertyNotify` stream.

## H
Distinct X11 properties encode A, B and heartbeat. The watcher uses raw X server event timestamps as monitor time. The byte-identical A3 monitor should agree with an independent raw-ledger oracle for POSITIVE, EXPIRE and NO_RESTART scenarios.

## T
Private fresh Xvfb+Tk sessions, separate watcher/publisher python-xlib Display connections, no XTEST or task input. Construction: one session per scenario. Formal after eligible construction: 12 fresh sessions, four reps/scenario. Source-first readback/freeze and exact-head #60 live lease are mandatory before any scientific X11 session.

## D
PASS formal only if12/12 sessions have exact expected atom sequence, nondecreasing X server timestamps, candidate/oracle agreement, POSITIVE SATISFIED4/4, EXPIRE EXPIRED4/4, NO_RESTART EXPIRED4/4, task_input_events0, cleanup/integrity/corruption gates pass, formal1/reruns0/replacements0/tuning0.

## C
PropertyNotify timing is backend transport evidence, not semantic application-effect readiness. X server 32-bit time is not assumed comparable to Python monotonic time.

## U
No rich-model/token/task/human-tempo/production claim.
