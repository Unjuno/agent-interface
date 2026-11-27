# V39 crash-recovery production topology audit

**Decision: `PASS_SOURCE_GRAPH`; production integration remains unimplemented.** This package statically audits current `main` source at base `668bafc28e706095ea25f9c27bdd53fd2f48c883`. The raw source graph checks are executable with `AUDITOR/audit_source.py`; pinned hashes are in `FREEZE.json`. No game, GUI, or session was launched.

## Current failure boundary

The outer `map01_overlap_controller_v39.py` launches one MAP01 session subprocess and tracks only that process. The default command selects `session_map01_v12.py`; the opt-in measurement path selects `session_map01_v15.py`. In either path, the session process constructs its `Backend` and `Executor`.

The V15 path swaps in Executor V13 and the typed/release-batch backend. That backend creates InputOwner V4/V12 using the session display. InputOwner V12 runs its Xlib owner loop in a daemon thread in the same host process; Executor V12's action worker is also a thread in that process. Normal `finally` cleanup closes Executor, backend/owner, game, and session in order. A hard death of the session process bypasses all of that cleanup.

On outer-controller failure, `ControllerFailureCleanup` first attempts a bounded `finish`, then may terminate or kill the tracked session process. It does not hold an X display connection or an independent input owner. The session `ready` message does not publish the display name, so the current parent/child protocol cannot establish an external owner without a handshake change.

This aligns with the experiments: hard-killing a co-resident Executor/owner process left the Xvfb key down (hard-kill A01), while a separate resident owner that observed Executor EOF successfully emitted keyup and verified keymap-up (supervised-owner A04). A04 validates that architecture under one child failure; it does not validate production wiring.

## Integration direction

The next production candidate should move the Xlib owner outside the session child failure domain. A dedicated owner service should outlive both the session/Executor process and, if controller-crash recovery is required, the controller itself. The session protocol should establish display identity and owner readiness before admitting any action. The session backend should use a narrow, versioned local RPC adapter with request IDs, exact operation schemas, key allowlists, lease/job identity, bounded deadlines, and no arbitrary commands.

When the session child exits or its RPC channel closes, the owner service should stop admitting new input, release its recorded keys/buttons, verify X server state, and publish an identity-bound recovery receipt. The parent must wait for verified recovery before reusing the display or starting a new session; a failed or unknown release should block reuse. Owner-service death needs a separate external policy, such as a supervisor that can restart the service and reset/recreate the display. Do not interpret executor terminal status or a KeyRelease event alone as proof of physical release.

## Required validation before integration can be called complete

- Exercise session v12 default and V15 opt-in through the new handshake, including no-action startup and ordinary key down/up.
- Kill the session child during one and multiple held keys; verify EOF, per-key releases, keymap-up, and the durable recovery receipt before reuse.
- Inject partial RPC writes, duplicate IDs, stale lease, focus change, keyup error, and owner service timeout; require fail-closed behavior and no silent session restart.
- Kill the owner supervisor/service and test the outer recovery policy. Verify orphan X server/game teardown and prevent another session from attaching until recovery is certified.
- Keep the current MAP01 live allocation unassigned until the isolated production-process tests pass and the authorized live lane is explicitly available.

Exact static checks and pinned source digests are in `results/source_audit.json` and `FREEZE.json`. This audit changes no production code and does not complete the computer-control goal.
