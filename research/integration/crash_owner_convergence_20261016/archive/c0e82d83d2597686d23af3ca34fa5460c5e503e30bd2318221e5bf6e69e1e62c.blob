# A26 outer-cleanup integration plan

Hypothesis: when the process-owned V15 input owner is SIGKILLed with exactly keys `a`, `d`, and Button1 held, the real `ControllerFailureCleanup.__exit__` path recognizes the dead owner generation, declines the absent normal receipt, executes guarded emergency recovery, persists the outer failure receipt, and sets `display_reuse_allowed=true` only after the ledger-bound emergency receipt verifies. It must retain the primary controller failure and leave unrelated cleanup-complete fields false when they were not established.

Scope: private TCP-disabled WSL2/Xvfb. The controller cleanup object is exercised; no model, game, physical input, or live MAP01 lane. One allocation, candidate once, no retries.

Decision: PASS only when down evidence, owner process death/generation, exact ledger state, release event/up state, emergency receipt hash binding, outer failure receipt emergency/display reuse flags, live session display during recovery, and clean Xvfb exit all agree. Otherwise preserve failure evidence.

Allocation ID: `V39-V15-PROCESS-OWNER-XVFB-A26-20261012-01`.
