# Retained v39 planner-boundary timing readiness

Decision: **BLOCKED_RETAINED_V39_TIMING_ENDPOINTS**.

One source-first deterministic retained-evidence classification was executed; primary invocations1, reruns0. No model, X11, MAP01 replay, task input or new data collection occurred.

## Result
Under the exact #1176 endpoint-completeness rule, **0/6** planner-boundary timing intervals are currently reportable from retained v39 evidence.

- `planner_wait`: unavailable because `planner_request` is not retained as an explicit typed endpoint, and clock provenance is absent.
- `response_to_accept`: both numeric roles are retained, but explicit `{clock_domain,clock_epoch}` is absent.
- `accept_to_input_ack`: both numeric roles are retained, but explicit clock provenance is absent.
- `input_to_useful`: `first_useful_effect` is not retained and clock provenance is absent.
- `observation_to_useful`: `first_useful_effect` is not retained and clock provenance is absent.
- `useful_to_terminal`: `first_useful_effect` is not retained and clock provenance is absent.

The retained #503 posthoc explicitly reports `stronger_task_effect_feedback=null` for every admitted v39 primary plan and states that viewport change, programmed input, terminal completion and run-level score are insufficient as a plan-bound useful-effect timestamp. Those values were not laundered into `first_useful_effect`.

## Minimum next instrumentation
A fresh separately leased live timing rung should retain, on one explicit comparable clock: (1) typed planner-request and planner-response endpoints; (2) action accept and input-ack endpoints; (3) observation-ready; (4) a **plan-bound independently scored first useful effect**; (5) terminal verification; and (6) `clock_domain/clock_epoch` metadata on every endpoint. Instrumentation overhead must be charged separately.

This does not invalidate older v39 timing descriptions at their original scope. It only says they cannot be promoted to the stronger #1176 planner-boundary timing vocabulary without new evidence.
