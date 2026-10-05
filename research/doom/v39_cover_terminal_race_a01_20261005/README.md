# V39 verified-empty cover terminal race A01

The current-main controller first interrupts the planner, sends a cancel for the active bounded cover, and waits for that cover's terminal. The old helper accepted only `status="cancelled"`. A matching `completed` or `expired` terminal with `release.verified=true`, `keys_down=[]`, and `buttons_down=[]` proves the cover is already terminal and neutral, but the helper raised and aborted the control loop. This is a controller liveness failure at the stop/replan boundary; it is not an input-safety bypass.

The frozen A01 probe extracted `cancel_invalidated_cover()` from main `018934cdf45fcabffcc4efe25b5c7b3d59bd459f` and reproduced the `completed_neutral` rejection. The candidate accepted that case only with a verified empty release; it continued rejecting nonempty completion and `failed` terminals. A portable replay and raw auditor v2 verify source bytes, the original as-run program/result, the reproduced matrix, operation order, matched cancellation ID, and three result corruption controls. The original A01 result and probe remain byte-preserved.

The runtime fix now treats `cancelled`, `completed`, and `expired` as possible terminal boundaries, while still requiring a verified empty release. `failed` and `needs_decision` terminals remain errors even with an empty release. Regression coverage exercises normal and optimized Python plus the adjacent paired-signal and duplicate-consistency suites.

Reproduce the retained probe and audit with:

```powershell
python research/doom/v39_cover_terminal_race_a01_20261005/reproduce.py
python research/doom/v39_cover_terminal_race_a01_20261005/audit_a02.py
python research/doom/test_map01_overlap_controller_v39.py
python -O research/doom/test_map01_overlap_controller_v39.py
python research/doom/test_map01_overlap_controller_v39_dual_signal.py
python research/doom/test_map01_overlap_controller_v39_pair_duplicate_consistency.py
```

This is source-composition and test-double evidence. It does not estimate race frequency or prove live input release, gameplay, threat response, useful feedback, bounded recovery, or MAP01 completion. The #59 fresh current-main threat-exposure allocation remains unassigned; this repair does not consume or replace it.
