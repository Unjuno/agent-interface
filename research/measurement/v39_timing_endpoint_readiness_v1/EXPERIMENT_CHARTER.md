# RETAINED-V39-TIMING-ENDPOINT-READINESS-20260918-001

## H
The retained MAP01 v39 evidence is not yet endpoint-complete for the six timing intervals validated by #1176. In particular, numeric timestamps that happen to exist in planner/runtime traces must not be promoted to named endpoints unless their retained schema gives the required role, source identity and comparable clock. The audit should identify exactly which intervals are reportable and which remain unavailable without a new live/instrumented allocation.

## T
Read-only retained-evidence audit in a disposable container. No model, GUI, X11, task input or replay.

Frozen interval vocabulary from #1176:
1. planner_wait = planner_request -> planner_response
2. response_to_accept = planner_response -> action_accept
3. accept_to_input_ack = action_accept -> input_ack
4. input_to_useful = input_ack -> first_useful_effect
5. observation_to_useful = observation_ready -> first_useful_effect
6. useful_to_terminal = first_useful_effect -> terminal_verified

Sources are exact retained Git evidence only:
- v39 report/runtime/planner protocol identities;
- #503 first-useful-feedback posthoc result/prereg;
- #1176 timing endpoint completeness contract/result.

For each endpoint classify RECORDED only if an authoritative retained field explicitly supplies that semantic role on a comparable monotonic clock. A nearby numeric timestamp is not a substitute. `visible_change` viewport receipts and health/ammo state transitions are not `first_useful_effect` because retained evidence explicitly denies plan-bound independently useful task effect attribution.

## D
`READY_RETAINED_V39_TIMING_ENDPOINTS_SCOPED` only if all six intervals have both endpoints RECORDED, same-clock and causally orderable for every admitted v39 primary plan in scope.

Otherwise retain `BLOCKED_RETAINED_V39_TIMING_ENDPOINTS` and report the exact unavailable endpoint roles/intervals. Any imputation from `model_ns`, neighboring protocol timestamps, viewport visible-change receipts, run-level score, or unbound state feedback is `FAIL_TIMING_EVIDENCE_LAUNDERING`.

## C
A retained field may be sufficient for its original experiment but not for the stronger #1176 timing role. Planner protocol receive timestamps may not equal an explicit planner-request endpoint. Application state change is not necessarily useful task effect. A future live instrumentation rung may close these gaps.

## U / stop
One read-only source/readiness audit. No latency/speed claim, no new measurement run, no MAP01 action, no model call. Stop after first deterministic source classification and independent audit.
