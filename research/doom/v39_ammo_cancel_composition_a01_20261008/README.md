# V39 ammo invalidation to planner cancellation composition A01

This construction probe joins the frozen current-main paired health/ammo monitor to the actual cancel-before-interrupt helper and persistent planner adapter. Health stays at 100 while ammo starts at 50 and is observed at either 1 or 0 during a pending answer.

## H/T/D/C/U

- **H:** Ammo 1 remains a soft change and preserves the pending answer. Ammo 0 hard-invalidates, requests executor cancellation before planner interruption, requires a verified empty terminal, and makes the old completed answer ineligible.
- **T:** Run the one-shot candidate once, then the independent audit and mutation tests. All current-main source identities are pinned in `FREEZE.json`.
- **D:** `PASS_CONSTRUCTION_COMPOSITION` only if the soft control avoids cancel/interrupt, zero ammo follows cancel → interrupt → verified empty terminal and the old answer remains ineligible, and a cancel-write failure still attempts interruption and remains an error.
- **C:** The monitor may label ammo zero as hard without that invalidation reaching the real planner lifecycle; transport ordering, terminal verification, or stale-answer rejection may fail.
- **U:** Synthetic values and fake transports do not establish real HUD timing, a correct tactical ammo floor, firing policy, physical release, useful feedback, recovery, or task outcome.

No game, model, GUI, OS input, or formal allocation is used. This complements the health-only composition and the separate ammo-only boundary probe; it does not replace live threat/recovery validation.
