# Calc save-controller receipt ordering — 2026-11-21

## Finding

The registered Calc profile records `task_save_request` inside
`CalcPrimaryProfile.verify_effect`, after `compiled_gui` captures
`effect_verification_started_ns` and before it captures
`effect_verification_accepted_ns`. The parent receipt builder required the
request timestamp to be earlier than the verification start. That condition
rejected a request produced by the verified callback itself.

The retained Docker trace demonstrates the ordering on the previous code:

| Event | Monotonic ns |
|---|---:|
| Effect verification started | 250643070026352 |
| Save request recorded | 250643070895201 |
| Effect verification accepted | 250643071183835 |

The request fell inside the verifier interval. The parser independently
matched the expected FODS cells, but `interface_verify_task` correctly kept
`task_success` unknown because the parent save-controller receipt was rejected.

## Change

- Validate `effect_verification_started_ns <= save_request_monotonic_ns <= effect_verification_accepted_ns`.
- Add a positive regression with the request strictly inside that interval and negative boundary cases for a request before start or after acceptance.
- Repair the composed Fake X fixture so the spawned owner has the Calc profile generation marker, negative OCR attempts receive their per-attempt mode, and nested `TestCase` cleanup runs in `finally`.

## Local validation

On the exact current-main source plus this candidate, read-only mounted in
`agent-interface-xvfb-mcp:late-input-r19`
(`sha256:bd191d30ea94871a1d3ca717252cd07a276e8ef7d1bcb4a130b63935ce075425`),
with network disabled, 2 CPUs, 4 GiB memory, and a 256 process limit:

| Gate | Normal | Optimized |
|---|---:|---:|
| Calc task-artifact suite | 20/20, 0.097 s | 20/20, 0.049 s |
| Registered Calc owned-process cases | 8/8, 23.649 s | 8/8, 22.923 s |
| Provider-to-public-MCP composition | 1/1, 12.147 s | 1/1, 12.479 s |
| Partial-input cancellation accounting | 1/1, 4.113 s | 1/1, 3.661 s |

All logs and the before-fix input trace are in `raw/`; `SHA256SUMS` covers the
packet and changed source hashes are recorded in `conditions.json`.

## Scope

This is a Fake X / synthetic provider-planner regression. No live GUI, external
provider, model API, formal allocation, or MAP01 action ran. The synthetic
profile's exact artifact scoring and release assertions pass, but this is not
live task success, broad recovery reliability, an efficiency result, or
Research Preview acceptance. Issue #57 remains open for its larger gates.
