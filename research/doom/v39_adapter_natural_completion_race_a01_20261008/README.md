

## A02: exact stdout reader race

A02 extends A01 through the production `CodexAppServerClient._read` JSONL reader. A matching `turn/completed` notification is sent first; its exact `wait_notification` consumer and the planner `await_turn` finish while the interrupt RPC response remains withheld. Only then is the correlated response delivered. The V39 invalidation helper subsequently accepts the simulated terminal only with a verified empty release receipt.

Result: `PASS_EXACT_READER_ROUTES_COMPLETION_BEFORE_INTERRUPT_REPLY`. The reader classifies the notification separately from the correlated reply; completion is consumed before the reply, and the invalidated answer stays ineligible. See `FREEZE_A02.json`, `RESULT_A02.json`, and `audit_reader_race_a02.py`.

This remains deterministic in-memory software composition. It does not measure actual App Server timing or OS/game input and does not close Issue #59's live threat, physical-release, useful-feedback, recovery, or MAP01 gate.

## A03: current-main re-freeze and rerun

After main advanced, A03 re-extracted the same three source blobs from exact commit `4a38cb226fd465bbf6b600b1e2f9aa20564f8e01`, verified their Git object IDs, and reran the A02 reader race in a clean temporary directory. The result again passes the A02 decision gate; its raw SHA-256 is recorded in `RESULT_A03.sha256`. Reproduce from a checkout containing that commit with:

```powershell
python -B research/doom/v39_adapter_natural_completion_race_a01_20261008/rerun_current_main_a03.py
python -B research/doom/v39_adapter_natural_completion_race_a01_20261008/audit_current_main_a03.py
```

The rerun confirms source-lineage stability and the same deterministic software result at the newer commit. It adds no live-runtime, physical input, useful-feedback, recovery, or game-outcome evidence; Issue #59 remains open.
