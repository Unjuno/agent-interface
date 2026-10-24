# R47 result

Disposition: `PASS_SCOPED` for one paired native-Windows fixture sequence; combined audit 13/13. Phase 1 strict release gate passed 11/11, then phase 2 ran on a distinct fresh fixture generation and the independent server-side oracle verified the exact task effect. Runtime-integrated `task_success` remains null; the positive claim is the separately bound external oracle result.

The repaired same-clock callback hold measured 1405.5285 ms after cancel response, above the preregistered 1400 ms planned hold. The exact call was polled 89 times during the hold (minimum 21); the same-generation Q-up was independently observed, with 74 eligible Q-up samples. The strict release audit passed all checks and the phase-1 hook, producer, fixture, and MCP session closed cleanly.

Phase 2 used a new fixture process, target generation, call, operation, oracle ID, and token. The external oracle observed `clicked=true`, `saved=true`, and the exact preregistered text. Its effect digest matched the fixture's effect-write timing sidecar. The fixture write-return to oracle observation interval was 253.5745 ms. This measures the recorded application write boundary to the separate oracle read observation; it is not physical durable-storage latency or an exact physical input-to-effect interval.

The attempt used one native Windows fixture and no WSLc or Docker. It does not establish MAP01 behavior, WSLc allocation eligibility, application transfer, matched efficiency, or broad reliability. R46 remains separately preserved as `FAIL_OR_UNKNOWN`; R47 has fresh IDs and raw evidence and does not overwrite or replay it.
