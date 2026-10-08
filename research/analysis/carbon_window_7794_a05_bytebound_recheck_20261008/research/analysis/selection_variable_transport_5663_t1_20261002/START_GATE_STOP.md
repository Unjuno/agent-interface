# Formal start-gate STOP — Issue 5663 T1 allocation 01

Allocation: SELECTION-TRANSPORT-5663-T1-20261002-01
Bounded CPU-only WSLc window recorded on #5085: 2026-10-02 03:20–03:25 UTC.
Disposition: STOP_BEFORE_CANDIDATE_MAIN_ADVANCED.

The frozen base main was f303f2f57baecd95f0dc5ef6bc063a29a63c90c3. During the same-window final remote-main check after the freeze sync was pushed, origin/main had advanced to 30f23e59c9d4637985fac7cae7abf008e2da1f62. The candidate was not invoked against the stale freeze. The exact in-command second was not retained by the shell session; the observation was during the assigned interval and before its 03:25 UTC end.

Counts: formal candidate=0, formal auditor=0, retries=0. No WSLc container was launched for this allocation; previously exited containers were left untouched. No GPU was assigned or used. This is a scheduling/provenance STOP, not METHOD_PASS, FAIL_METHOD, or a transport result.

Construction remains separate: the host-only candidate/auditor passed the finite controls in construction attempt 03; this does not replace the frozen WSLc execution or satisfy the allocation's formal decision gate. Preserve attempts 01–03 and the original freeze/main values. This allocation is terminal; no refreeze, retry, or replacement window is requested.
