# VISUAL-CONTEXT-A01 — pending answer after changed frame

**H:** When the exact retained consecutive MAP01 frames at source sequence 2 and current sequence 3 have identical typed health/ammo (97/48) and pointer binding but different RGB hashes, current-main `DoomCoverSignalPairMonitor` will not invalidate the pending planner turn; after a synthetic completed answer, `prepare_action_admission` will report the action executor-ready because its freshness contract checks typed health/ammo and binding, not the changed image identity. An unchanged-frame hash control should behave identically.

**T:** Freeze current-main `f185a9059d485a4f8d5a65e9e7f6782897f67eae` source functions and the exact retained event/frame pair. Feed the real paired typed signal row through the current monitor while the real `PersistentPlannerAdapter` fake client is awaiting. Then run the controller's actual final admission helper on the fresh same-epoch health/ammo. Compare changed-frame and same-hash control arms. One WSLc CPU run.

**D:** The hypothesis is supported for the software boundary if both arms remain eligible and `READY_FOR_FRESH_EXECUTOR_ADMISSION`, showing the image-hash change does not alter monitor/final-admission outcome. If changed-frame arm invalidates or is rejected, hypothesis not supported. No executor admission/authority is ever invoked.

**C:** The selected real frames may differ only by routine animation or viewpoint motion; hash change is not proof of a threat or stale semantics. This is a boundary characterization, not evidence the accepted action would be wrong.

**U:** Historical retained frames/raw rows plus synthetic planner response; original run's controller source was not pinned to current main. The software under test is exact current main, but no current-main game execution/model inference occurred. No live threat effect, recovery, physical input, task success, or MAP01 completion claim.
