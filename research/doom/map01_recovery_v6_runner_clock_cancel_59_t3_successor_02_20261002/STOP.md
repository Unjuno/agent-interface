# T3U construction STOP — candidate not invoked

Allocation: `MAP01-V6-RUNNER-CLOCK-CANCEL-59-T3U-20261002-01`  
Base: `97afcb82f90616589801a256893f886010ed6d27`  
Candidate invocation: 0; construction invocation: 1; retries: 0.

## Observed

- `python3 -m unittest discover -s research/doom/map01_recovery_v6_runner_clock_cancel_59_t3_successor_02_20261002 -p 'test_*.py' -v`: 7/7 pass.
- `py_compile` for candidate, auditor, and tests: exit 0 (the command chain advanced to construction).
- `python3 .../run_experiment.py --construction`: exit 1, stdout `construction gate failed`.
- No candidate scenario and no independent raw audit ran. The construction code did not persist a structured row on failure, so the precise failing predicate is not proven from retained run output.

## Source-level diagnosis and boundary

The construction gate requires `fallback_terminal_status == "cancelled"`. But the mock backend's `execute()` observes the Lease cancel event and returns normally; exact Executor-v10 increments the completed-step count and leaves terminal status `completed` unless `Cancelled` is explicitly raised. Thus the expected status is inconsistent with the current candidate's cooperative-return mock. This is a confirmed design defect in the gate/mock pairing, but because the failed construction row was not retained, do not infer that it was the only failed predicate or claim the rest of the construction gates passed.

Decision: `STOP_CONSTRUCTION_GATE_MISMATCH_RAW_INCOMPLETE`. This is not evidence for or against H and is not a candidate FAIL. Preserve T3U unchanged; no retry, no formal allocation consumed. Any corrected gate must be a separately frozen successor and should retain the construction row and stderr/stdout before evaluating predicates.

## Scope

No container, game, GUI, model, GPU, network, or input was invoked. The 7/7 mutation suite validates only the auditor's synthetic raw checks. No claim about transport, MAP01, gameplay, threat response, physical occupancy, or #59 completion.
