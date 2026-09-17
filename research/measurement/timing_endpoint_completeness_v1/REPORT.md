# Timing endpoint completeness — first outcome

Task `TIMING-ENDPOINT-COMPLETENESS-CONTRACT-20260918-001`, Issue #1176, parent #46.

## Decision

**`PASS_TIMING_ENDPOINT_COMPLETENESS_SCOPED`**

This is a deterministic reporting-contract experiment only. No model/provider/network/GUI/X11/task-input/shared-runtime action occurred.

## Frozen factor

The same planner-boundary timing envelopes were evaluated under:
- `NAIVE_FALLBACK`: substitute the nearest recorded timestamp for a missing declared endpoint and numerically subtract cross-clock timestamps;
- `TYPED_ENDPOINT_GATE`: report a numeric interval only when both declared endpoints are RECORDED, share exact clock domain+epoch, and satisfy nonnegative causal order.

Frozen interval vocabulary:
- planner_request -> planner_response
- planner_response -> action_accept
- action_accept -> input_ack
- input_ack -> first_useful_effect
- observation_ready -> first_useful_effect
- first_useful_effect -> terminal_verified

Timing metadata grants no authority and does not verify task success.

## Formal first outcome

One frozen formal invocation, reruns0, seed `117620260918001`.

- rows: **300,000**
- 12 exact strata × 25,000 rows
- fixed controls: **12/12**
- candidate/oracle mismatch: **0**
- valid exact-width errors: **0**
- candidate numeric claims on missing/NOT_RECORDED/cross-clock/reversed/malformed evidence: **0**
- authority promotions: **0**
- task-success promotions: **0**
- baseline `NAIVE_FALLBACK` numeric claims on invalid strata: **275,000**

The baseline number is a deliberate negative discriminator, not a claim about a production implementation. It shows that numeric timestamps alone are insufficient when endpoint identity, missingness and clock provenance are ignored.

## Integrity

- RESULT SHA-256 `fa4a48db7516379d0ddab91ed950f78985afc9e8725b3eb76c52ae3f797d4536`
- AUDIT SHA-256 `20fef1d34892ee4694acea82688d0a6661cf0f311af64fc6ab8f645689a87c81`
- CORRUPTION SHA-256 `bac13af5fe22a873d2e2317f123f0ff33760bc825cc8420cf34162beceea2078`
- SOURCE_REHASH SHA-256 `0e93c8eeb6529d9a2e832dbc6339b039df0a454c41fd3b715fbce29feaf37d64`
- independent audit: PASS/errors[]
- copied-result corruptions: 6/6 rejected
- frozen source rehash: 6/6 exact

## Boundary

This closes only endpoint-completeness and same-clock admission semantics for timing reports. It does not establish real timestamp collection overhead, clock synchronization, actual model latency, Calc/OpenTTD end-to-end attribution, or optimization benefit.

A future #46 live instrumentation rung should first retain authoritative observation/planner/runtime/effect endpoints and explicit clock identities. Missing endpoints must remain missing rather than being reconstructed from neighboring local timestamps.
