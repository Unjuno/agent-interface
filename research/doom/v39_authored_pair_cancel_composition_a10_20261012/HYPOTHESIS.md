# A10 — actual HUD guard through pending-answer cancellation

Freeze time: 2026-10-12 before the WSLc run. Source commit is current main `f185a9059d485a4f8d5a65e9e7f6782897f67eae`; exact controller, guard, and planner-adapter blobs are in `FREEZE.json`.

**H:** A paired health hard-floor crossing emitted by the real current-main `DoomCoverSignalPairMonitor`, delivered through the actual controller wait closure during a pending turn, will cause `cancel_invalidated_cover` to write and flush executor cancel before requesting planner interruption. Even if the fake server later reports the interrupted old turn as completed, the production `PersistentPlannerAdapter` will keep its answer ineligible, and the terminal helper will accept only an explicitly verified empty-release receipt.

**T:** AST-extract exact controller guard specs, pair monitor, nested wait closure, and cancellation helper. Load the exact guard class and planner adapter from frozen current main. Feed source health/ammo 70/6 at sequence 10, then typed paired health 64/ammo 6 at sequence 11 against health floor 65 while a planner turn is pending. Block interrupt ACK, queue a canceled terminal with verified empty keys/buttons, release the ACK, and inspect write/flush/interrupt order, answer eligibility, and terminal release validation. Run the frozen test once in WSLc with networking disabled, one CPU requested, 512 MiB requested.

**D:** PASS_SCOPED requires real guard invalidation, `cancel write → flush → interrupt request → interrupt ACK`, canceled/unavailable old answer even if the fake service says completed, and a validated empty-release terminal. Any ordering or state mismatch is FAIL_SCOPED; source identity mismatch is HOLD.

**C:** The adapter and controller functions run against in-memory queues, a fake executor, and a delayed fake planner client. A synthetic terminal receipt cannot establish OS input delivery, physical key release, owner reconciliation, or real service scheduling.

**U:** No Doom, GUI, model, App Server, OCR, OS input, physical release, useful feedback, bounded wall-clock recovery, ammo/progress effect, terminal game result, human-tempo result, or live allocation was tested. This is a composed source-boundary result only.
