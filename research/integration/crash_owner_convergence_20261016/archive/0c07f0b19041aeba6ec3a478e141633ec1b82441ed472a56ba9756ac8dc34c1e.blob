# A16 plan

Hypothesis: after a process-owned V15 input owner is killed while two keys and Button1 are held, the integrated outer recovery path can reconstruct intended inputs from the fsynced ledger, confirm the service process identity is dead, bind release to unchanged focus/surface/geometry and pointer location, release only recorded inputs, observe release events and empty X state independently, and write a durable emergency receipt.

Scope: private TCP-disabled Xvfb only; no game, model, or physical input. This tests the recovery primitive and cleanup integration boundary, not full V39 product success.

Decision rule: `PASS_LEDGER_BOUND_EMERGENCY_RECOVERY` only if the input owner emits a matching ready identity, independent probes observe both keys and Button1 down before SIGKILL, the service is confirmed dead by PID plus start ticks, ledger reconstruction retains exactly `a`, `d`, and Button1, recovery emits only releases for these inputs, the independent observer sees each release and key/button state is up, and the durable receipt binds the ledger hash and reports verified. Any failed gate is retained as STOP/FAIL; no retry.

Allocation: `V39-V15-PROCESS-OWNER-XVFB-A16-20261012-01`; candidate invocations allowed 1; retries 0; auditor invocations 1. Source hashes and environment are frozen in `FREEZE.json` before candidate invocation.
