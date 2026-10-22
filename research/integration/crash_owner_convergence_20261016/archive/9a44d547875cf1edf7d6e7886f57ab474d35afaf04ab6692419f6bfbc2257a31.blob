# A31: full outer cleanup completion over the real process-owner child

Hypothesis: on a private TCP-disabled Xvfb display, a child using the actual opt-in V15 process-owner backend can be asked to finish by the real `ControllerFailureCleanup.__exit__`; the cleanup can observe scorer completion, reap the child, retire its stdout reader, and accept the generation-bound fsynced normal owner-close receipt, resulting in `cleanup_complete=true` and display reuse allowed.

Treatment: real backend and owner service in a real child process; actual cleanup class and bounded finish pipe; no input operation. Score and owner-events files plus `post_control_score` are synthetic protocol fixtures because this candidate isolates cleanup integration and does not run the V39 CLI/scorer. Planner is a test double. No game, model, physical input, or live MAP01.

One candidate invocation, no retries. PASS requires all cleanup-complete fields and all recorded stages returned; child exits 0; stdout reader exits without errors; owner receipt PID/start ticks/owner ID match the ready event; receipt is fsynced, verified-empty, and accepted by the normal receipt gate; Xvfb exits 0. Preserve any failure as STOP/FAIL and do not rerun this allocation.

Allocation: V39-V15-PROCESS-OWNER-XVFB-A31-20261012-01.

This is a distinct allocation after A28 stopped before exercising cleanup because the host X11 socket directory was a read-only, non-sticky mount. Preflight validated a private user/mount namespace with isolated tmpfs /tmp; no shared X11 resources are changed.


A29 stopped after the child import failed because this minimal environment has no Pillow installation. This allocation includes explicit fail-closed import stubs for image capture and the unused GUI catalog, matching the existing process-owner Xvfb harness; snapshot/image-capture calls remain forbidden by the stub.


A30 established the isolated Xvfb namespace but timed out before the backend ready event. This diagnostic allocation preserves the same treatment and adds raw stdout-line/event capture and child state to distinguish output framing from backend or process-owner startup. It is one invocation, no retries.

