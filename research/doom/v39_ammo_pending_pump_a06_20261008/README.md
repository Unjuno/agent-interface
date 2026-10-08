# V39 ammo invalidation through pending observation pump A06

This one-shot construction test extends the health-only pending-pump case by feeding a paired typed ammo-zero observation through the frozen current-main wait dispatcher and pending-future loop. Health remains 100; source ammo is 50 and the queued observation reports ammo 0.

## H/T/D/C/U

- **H:** The pending-future loop dispatches the typed pair to the actual V39 ammo monitor while the planner future is pending. Ammo zero invalidates the pair, triggers executor cancel before planner interrupt transport, and is followed by a terminal row with verified empty keys/buttons.
- **T:** Run the frozen source-slice candidate once, then audit its saved event stream and run mutation tests. Source commit, blobs, and hashes are pinned in `FREEZE.json`.
- **D:** `PASS_CONSTRUCTION_EVENT_PUMP` only if the event queue delivers the pair while the future is pending, the monitor reports `ammo:below_hard_minimum` without input authority, cancellation precedes interrupt transport, and verified empty terminal dequeue follows.
- **C:** The queue dispatcher could miss paired ammo changes or fail to hand the hard invalidation to cancellation while the planner is pending.
- **U:** Synthetic rows and deterministic fakes do not establish HUD accuracy/cadence, live timing, physical release, tactical threshold correctness, useful feedback, recovery, or game outcome.

The independent direct-helper composition is preserved in `v39_ammo_cancel_composition_a01_20261008/`; this experiment tests the additional queue-dispatch link. No live allocation, game, model, GUI, or OS input was used.
