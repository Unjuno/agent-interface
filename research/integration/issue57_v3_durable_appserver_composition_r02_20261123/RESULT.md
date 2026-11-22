# Issue #57 ProspectiveRun lifecycle boundary R02 — result

## Outcome

**PASS_FAIL_CLOSED_INCOMPLETE_ENVELOPE_BOUNDARY**, four successful harness executions: two normal and two under `-O` (all exit 0). Each mode was executed twice with fresh local evidence roots; each run recorded four assigned rows: success-shaped, failed with known synthetic usage, deferred with known synthetic usage, and failed with usage UNKNOWN. Every row remained HOLD; run finalization remained HOLD with the other 14/18 assignments explicitly missing; `run-manifest.json` retained `dispatch_enabled: false`. All four raw caller envelopes and classifications are in each `lifecycle.jsonl` and `adjudication.json`.

## Important scope limit

This fixture supplied deliberately incomplete caller envelopes and no registered durable task custodians. The observed projection reason for each row was `task_telemetry_incomplete`; custody independently reported `task_custody_missing`. Therefore this is only a lifecycle recording/fail-closed boundary check. It does **not** exercise four authentic v3 caller results, distinguish successful from failed provider attempts in the projector, prove token-usage joins, or connect dispatch/adapters. It is not a complete ProspectiveRun join and does not authorize live dispatch. The failed harness setup attempts are retained separately and are not counted as passes.

## Harness setup failures preserved

- First attempt: source root defaulted to the parent task workspace, so pinned source hashing stopped with `FileNotFoundError` before the prospective run could start.
- Second attempt: after correcting the source root, the same evidence root was already created by the first constructor before source-manifest assembly; fail-closed `FileExistsError` was correct. A new `*-rerun1` evidence root was used for the successful runs.

## Reproduction and custody

The exact inline harness is `run_fixture.py.txt`. Conditions are in `CONDITIONS.md`; raw streams and exit codes are stored as `normal.*` and `optimized.*`. The incomplete roots from setup failures are retained as-is when they contain files; no result was inferred from them. Each successful run preserves its allocation, run manifest, lifecycle journal, and adjudication in `normal-rerun1/`, `optimized-rerun1/`, `normal-rerun2/` and `optimized-rerun2/`.

This local synthetic result narrows the current boundary but leaves Issue #57 open. Next, use actual v3 outputs and their provider-attempt/usage envelopes with registered durable task custody, including success, failure, deferred, and unknown usage; only then assess whether any live three-arm allocation is admissible.
