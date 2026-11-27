# Visual-context freshness boundary A01 — WSLc result

Decision: **PASS_CONSTRUCTION_VISUAL_FRESHNESS_BOUNDARY**. The single frozen WSLc test run passed 2/2 tests under Python 3.14.8 in image `sha256:4fc7258eb9f2430d573bcbd352fc9851eee6ce96a65ff026274dfb317119bb7b`.

Using adjacent retained V39 observations with identical typed health/ammo (97/48), the changed-frame case had different source/current PNG and decoded-RGB hashes. The current-main paired health/ammo monitor emitted no invalidation; the synthetic pending planner answer remained eligible and final action validity returned `READY_FOR_FRESH_EXECUTOR_ADMISSION`. Both `executor_admission` and input authority remained absent. The same-hash control reached the same result. The independent audit verified the frozen files and input Git blobs against the then-current `origin/main` source closure and reconstructed both result rows from the saved WSLc log.

This exposes a bounded visual-freshness limitation: image identity change alone is not a V39 health/ammo invalidation signal. It does **not** show that the pixel difference is a threat, that the response is unsafe, or that an executor would admit/send the action. The historical V39 event trace's original controller source was not pinned, although every tested source and fixture blob in this A01 closure matches current main. The planner is synthetic; no model, game, OS input, physical release, threat policy, recovery, or task effect ran. This construction result does not satisfy Issue #59's live threat-exposure gate.

Raw command output, exit status, image identity and before/after container inventories are preserved in `results/a01-01/`. WSLc warned that cgroup/swap limits are unavailable; no hard memory enforcement is claimed.
