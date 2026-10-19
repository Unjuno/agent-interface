# A14 result — pending-turn ammo staleness

The final frozen WSLc run passed 2/2 cases. The persistent adapter received the prompt at source ammo 6. Its deterministic fake client's completion wait published a newer observation at sequence 11. When ammo was 4 and the synthetic eligible action required minimum 5, current-main final action admission returned `REJECTED_ACTION_NOT_CURRENT` / `ammo_minimum_failed`. When ammo stayed 6 in the same new observation epoch, it returned `READY_FOR_FRESH_EXECUTOR_ADMISSION`. Both receipts retained `executor_admission=null` and `input_authority_admitted=false`.

Disposition: `PASS_CONSTRUCTION_ONLY_PENDING_TURN_FRESH_ADMISSION`. This shows that this software boundary rechecks current typed ammo after a pending planner turn. It does not establish live sensor fidelity, model behavior, OS/game input, policy reaction, recovery, useful effect, survival, or MAP01 completion. The current Issue #59 live allocation remains unassigned.

WSLc warned that swap limit capabilities are unsupported; memory was limited without swap. No cgroup enforcement claim is made.
