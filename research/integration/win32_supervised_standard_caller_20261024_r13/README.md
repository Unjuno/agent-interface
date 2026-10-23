# Win32 supervised standard MCP cancellation and bounded close drain — R13

R13 is a one-shot local Windows trial through the public stdio-MCP caller,
frozen at source `3af0a4563c50f64e93e77e3fbed5c63996c1fe3d`. It tests the R12
repair: a dispatch worker must leave the shared operation lock after cancellation
reaches recovered/unknown, allowing public session close to complete before the
finite four-second drain ends.

The runner preserves R12's exact public call sequence: record a possible initial
pre-admission `unknown_call`, poll the returned call ID, wait for injected
Q-down, verify same-call `running`, send one cancel, then verify exact producer
exit, recovered release, independent same-generation Q-up, saved fixture effect,
and bounded public close. Every poll and close response is retained. Only
explicit `busy` close responses may be retried at 100 ms intervals. PASS requires
closed session and complete local cleanup. A mismatch is frozen as
FAIL_OR_UNKNOWN; there is no replay or rerun.

The only resources are this user-authorized Windows PC and one owned fixture.
No WSLc or Docker allocation is used. Runtime `task_success` remains unclaimed;
this result cannot establish MAP01, matched efficiency, or broad reliability.
