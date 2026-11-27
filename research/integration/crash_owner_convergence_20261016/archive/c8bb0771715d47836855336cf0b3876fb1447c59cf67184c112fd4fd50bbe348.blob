# A28: full outer cleanup completion over the real process-owner child

Hypothesis: on a private TCP-disabled Xvfb display, a child using the actual opt-in V15 process-owner backend can be asked to finish by the real `ControllerFailureCleanup.__exit__`; the cleanup can observe scorer completion, reap the child, retire its stdout reader, and accept the generation-bound fsynced normal owner-close receipt, resulting in `cleanup_complete=true` and display reuse allowed.

Treatment: real backend and owner service in a real child process; actual cleanup class and bounded finish pipe; no input operation. Score and owner-events files plus `post_control_score` are synthetic protocol fixtures because this candidate isolates cleanup integration and does not run the V39 CLI/scorer. Planner is a test double. No game, model, physical input, or live MAP01.

One candidate invocation, no retries. PASS requires all cleanup-complete fields and all recorded stages returned; child exits 0; stdout reader exits without errors; owner receipt PID/start ticks/owner ID match the ready event; receipt is fsynced, verified-empty, and accepted by the normal receipt gate; Xvfb exits 0. Preserve any failure as STOP/FAIL and do not rerun this allocation.

Allocation: V39-V15-PROCESS-OWNER-XVFB-A28-20261012-01.
