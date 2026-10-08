

## A02: exact stdout reader race

A02 extends A01 through the production `CodexAppServerClient._read` JSONL reader. A matching `turn/completed` notification is sent first; its exact `wait_notification` consumer and the planner `await_turn` finish while the interrupt RPC response remains withheld. Only then is the correlated response delivered. The V39 invalidation helper subsequently accepts the simulated terminal only with a verified empty release receipt.

Result: `PASS_EXACT_READER_ROUTES_COMPLETION_BEFORE_INTERRUPT_REPLY`. The reader classifies the notification separately from the correlated reply; completion is consumed before the reply, and the invalidated answer stays ineligible. See `FREEZE_A02.json`, `RESULT_A02.json`, and `audit_reader_race_a02.py`.

This remains deterministic in-memory software composition. It does not measure actual App Server timing or OS/game input and does not close Issue #59's live threat, physical-release, useful-feedback, recovery, or MAP01 gate.
