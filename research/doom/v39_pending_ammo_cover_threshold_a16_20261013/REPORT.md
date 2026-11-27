# V39 pending ammo soft/hard boundary A16 — WSLc result

Decision: **PASS_CONSTRUCTION_SOFT_HARD_PENDING_TURN_BOUNDARY**. The one frozen WSLc run passed 2/2 tests under Python 3.14.8 in image `sha256:3fdfb56e36e335629eb0442de560c4d78a199dd7443ad99de6c33cfab087460d`. All eight frozen source files match current `origin/main` at `964c9197d5083ab55ea7fdc9105427623e89e677` by byte hash and Git blob identity. The independent audit re-parses both arm outputs and checks the ordered event/result fields.

With source ammo 6 and a policy minimum of 5, a pending-turn observation at ammo 4 remained a soft cover event: the planner answer stayed eligible, but fresh final admission rejected the action as `ammo_minimum_failed`. At ammo 0, below the authored cover floor 1, the monitor produced `HARD_INVALIDATED`, requested a new decision, and invoked the interrupt callback before the fake wire-completed response could become eligible; the adapter rejected that late answer. Neither arm produced executor admission or input authority.

This confirms the tested software boundary respects the authored thresholds. It does not establish that floor 1/minimum 5 is tactically correct, that cancellation physically releases input, or that the guard improves survival or task outcomes. The client/answers were synthetic; no model, game, GUI, OS input, physical release, recovery, threat effect, or live allocation ran. WSLc warned host cgroup/swap enforcement is unavailable, so no hard memory cap is claimed.

Raw output and exit status are under `results/a16-01/`; the exact frozen image sources, `FREEZE.json`, original pending run note, image inspection, command, run record, independent audit, and checksums are retained in this package.
