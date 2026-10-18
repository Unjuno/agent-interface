# V39 paired ammo validity boundary A01

This one-shot synthetic construction probe exercises the frozen current-main V39 `build_cover_monitor` with health stable at 100 and ammo falling sequentially from 50 to 39, then 1, then 0. It tests what the existing paired typed-HUD guard treats as a soft change versus a hard invalidation; it does not claim that any particular ammo threshold is tactically correct.

## H/T/D/C/U

- **H:** The current fire-cover ammo guard has hard minimum 1. Ammo 39 and 1 should be soft changes that preserve the cover and enter soft-event telemetry; ammo 0 should request a new decision.
- **T:** Run `python -B candidate.py` once, followed by `python -B audit.py` and `python -B -m unittest -v research.doom.v39_ammo_validity_boundary_a01_20261008.test_audit`. Source and motivating triage identities are pinned in `FREEZE.json`.
- **D:** `PASS_CONSTRUCTION_BOUNDARY` only if the frozen actual builder/paired monitor emits the expected 39→1 soft events and 0 hard invalidation, with unchanged health and no input authority.
- **C:** A pair-coherence, source-binding, sequence, or stale-source condition could invalidate earlier or fail to invalidate at zero.
- **U:** Synthetic values do not establish real HUD latency, a proper tactical ammo floor, whether firing should stop before zero, interruption/physical release, useful feedback, recovery, survival, or task outcome. The historical 50→37 ammo change is a surrounding-window association; it does not locate consumption during the pending call.

The output, independent audit, failed-claim mutation tests, source identities, command, and manifest are preserved in this package. No game/model/GUI/OS input or formal allocation is used. The separate live threat/recovery gate remains required.
