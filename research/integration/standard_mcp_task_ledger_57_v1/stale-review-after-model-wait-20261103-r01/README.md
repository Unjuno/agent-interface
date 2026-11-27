# Issue #57 stale Calc review experiment — r01 (pre-fix observation)

This retained Fake X run preceded the public-MCP stale-source preflight. After the reviewed sequence was superseded during the simulated wait, the registered profile reached the owner worker and returned `runtime_failed`; its response had `operation_invoked=true`, `input_dispatched=null`, `release_confirmed=false`, `cleanup_status=UNKNOWN`, and `late_server_request_possible=true`. No `calc-fake-state.json` input-state artifact was created, and the owner snapshot listed no held keys/buttons.

This result did not prove a dispatched input, but it also did not provide a clean typed pre-admission refusal. That uncertainty prompted the parent snapshot check retained in r02. Do not read this pre-fix result as the final behavior. Raw calls, receipts, changed title cue, and the nested source hash manifest are retained under `stale-review-after-model-wait/`.

Synthetic environment only; no model/provider request, physical Calc, WSLc, MAP01, or efficiency comparison.
