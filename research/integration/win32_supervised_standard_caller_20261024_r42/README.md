# R42 — CUA foreground-gated bounded recovery and fresh task oracle

Status: prepared; no R42 fixture or input has started.

R42 tests whether a CUA activation of the exact owned native fixture window, followed by an independent `GetForegroundWindow` equality check, changes R41's queued-before-backend result. The attempt is one-shot. Phase 2 uses a separate fixture, session, target generation, action and oracle receipt, and starts only after the strict phase-1 release gate passes.

Every run requires an input-free preflight, absent output and marker paths, exact frozen sources and predecessor hashes, one dispatch, no replay, bounded activation waits and foreground restoration. An activation mismatch or timeout fails closed. Native-PC evidence does not establish WSLc, MAP01, broad reliability, matched efficiency or real-application transfer.
