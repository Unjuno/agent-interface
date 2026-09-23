# #3266 repeated stale-control checks v1

Decision: PASS_STALE_CONTROLS_REPEAT_SCOPED

## H/T/D/C/U

- H: Across independent p1→p2 display generations, the composite stale controls reject terminated p1 state even when XID is reused.
- T: Two fresh cycles in one pinned Debian/Chromium/Xvfb/Openbox container. Each cycle starts p1 on a fresh display/profile/CDP port, records p1 page target and XID, terminates p1 and destroys the display, starts p2 on a fresh display/profile/CDP port, records p2 XID, checks old PID liveness and attempts old CDP target connection.
- D: Retain per-cycle XIDs, old-process liveness, old-target rejection and per-cycle decision. No input is sent in this repetition; the prior combined input/effect PASS remains separate.
- C: Scoped PASS requires every cycle to have old_process_alive=0, old_target_rejected=1, and explicit XID reuse observation.
- U: Two cycles only; no statistical reliability claim, no multi-app coverage, no new p2 application effect, no production integration.

## Obstac result

- Cycle 1: p1 XID 4194307, p2 XID 4194307, old_process_alive=0, old_target_rejected=1, PASS
- Cycle 2: p1 XID 4194307, p2 XID 4194307, old_process_alive=0, old_target_rejected=1, PASS

Both repeated cycles rejected stale p1 authority despite XID reuse.

## Scope

This strengthens the previously retained composite identity evidence for the pinned Chromium/Xvfb fixture. It does not establish all process/display race classes, cross-application reliability, or product readiness. The next broader acceptance gate must combine repeated stale controls with repeated positive p2 input/effect receipts under a frozen allocation.
