# Issue #57 prospective durable provider join — R03

## Frozen scope
- Main base: `490d7bcb4d84927116112e5ff348cdeadfc489d6`; candidate branch at execution: `research/win32-expired-authority-delayed-effect-r24-20261123` with prior head `7e3f9bf3ed7237bc7ba3fdf183b0ebb3c8e0977d` plus this focused test change.
- Windows CPython 3.13.14; Pillow 12.2.0.
- One synthetic App Server peer, one failed grounding answer, one assigned `plain/task-1` row, a fresh local prospective-run evidence root and its registered durable custodian.
- No real provider, GUI, native input, Docker, WSL, external allocation or live dispatch.

## PASS rule
The exact turn/thread identity and all five token counters must survive the App Server JSONL client, grounding model, v3 adapter, public caller, durable Calc custodian and ProspectiveRun lifecycle journal. Custody audit must return `audited`; the v1 task projection must remain HOLD for the failed model attempt; finishing 1 of 18 assignments must remain HOLD with 17 missing; manifest dispatch remains disabled. Run the complete test module normally and under `-O`.

## Results and retained failures
- Final fixed module: 3/3 pass normally and 3/3 pass under `-O`; exit 0 both.
- The first test version incorrectly looked for custody data in the projection return object. Both modes failed with `KeyError: 'custody'`. The assertions were corrected to read the durable lifecycle event, where custody is recorded by contract; original failure output is retained as `initial-failure.*` and excluded from pass counts.
- The passing test confirms durable custody audit succeeded with `turn-ledger-1`, `thread-ledger-1`, and 1,234 input tokens. The projection correctly remains `HOLD / failed_attempt_not_representable_in_v1`; the run remains `HOLD / assigned_task_missing` with 17 missing rows.

## Scope limit
This closes one synthetic failed-provider join into ProspectiveRun's registered durable task custodian. It does not exercise successful answers, deferred completion, unknown usage through the authentic caller, all 18 tasks, the other comparison arms, a real provider or GUI, nor enable dispatch. It is not an efficiency or task-success result. Keep Issue #57 open.
