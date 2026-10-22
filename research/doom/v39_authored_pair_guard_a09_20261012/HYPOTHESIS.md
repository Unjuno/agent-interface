# A09 — authored paired HUD guard threshold crossing

Freeze time: 2026-10-12, before the WSLc test invocation. Scope is current main `f185a9059d485a4f8d5a65e9e7f6782897f67eae` and the exact controller/guard blobs listed in `FREEZE.json`.

**H:** The current V39 paired health/ammo cover monitor, with its real one-way `ObservableSignalGuard`s, invalidates a cover when an authored health hard floor is crossed, when ammo reaches the monitor's positive floor, or when health/ammo evidence belongs to different epochs. In-envelope same-epoch changes should remain soft and non-authoritative.

**T:** AST-extract the production `guard_spec`, `ammo_guard_spec`, pair-validation helpers, and `DoomCoverSignalPairMonitor` from the frozen current-main controller. Construct real guards with the frozen `ObservableSignalGuard`. Run four deterministic cases: health 70→64 against effective floor 65; ammo 6→0 against floor 1; health/ammo 70→68 and 6→5 within the envelope; and a mixed-sequence pair. Execute once in WSLc, network disabled, one CPU requested, 512 MiB requested.

**D:** PASS_SCOPED requires health and ammo boundary cases to request a new decision with no authority grant, the positive control to return no invalidation while recording soft changes, and mixed epoch evidence to fail closed. A mismatch is FAIL_SCOPED; source identity mismatch is HOLD.

**C:** The monitor may only emit invalidation evidence; the controller wait/cancel path and input-owner release are separate behaviors. Synthetic typed signals may conceal OCR errors, transport timing, or queue-order races.

**U:** No live Doom, model, GUI, OCR, process interruption, physical key release, useful feedback, recovery, task effect, terminal outcome, human-tempo, or allocation was tested. This does not establish end-to-end control. The ammo guard tested here enforces the monitor's positive floor of 1; it does not test a planner-authored higher ammo minimum.
