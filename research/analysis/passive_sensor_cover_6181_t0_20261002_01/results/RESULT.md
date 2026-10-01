# Allocation result — passive sensor cover T0

**Disposition: PASS_METHOD_SCOPED** (finite synthetic method test only).

- Candidate: one invocation, exit 0, 2026-10-01 18:44:12.997–18:44:13.260 UTC.
- Independent raw-only CPU auditor: one separate invocation, exit 0, 18:44:22.753–18:44:22.984 UTC.
- Retries: 0. Construction attempt 01's harness-only failure remains retained; refreshed construction attempt 03 passed 7/7 plus AST parsing.
- All 16 channel subsets were enumerated and independently recomputed; audit errors=0.
- Unique minimum: `{app_status, os_focus_input}`, synthetic cost 7; full bundle cost 11; declared greedy selected `{app_status, crop, os_focus_input}`, cost 8.
- Screenshot-only and impossible effect-alias controls returned `NO_SUFFICIENT_PASSIVE_COVER`.
- Dropping either selected producer (app or OS) returned no-cover. Four raw-audit mutation controls were rejected: crop falsely independent, missing observation, stale generation, and dispatch-only substituted for effect.
- Exact candidate/auditor raw JSON, hashes, source identities and invocation timestamps are retained beside this report.

## Execution boundary and limitations

Ran on local Windows 10 / CPython 3.11.9 CPU only. No container/WSL, GPU, model, network, GUI, user data or OS input was used. The frozen state table, response classes, producer lineage and integer channel costs are synthetic/stipulated. This does not establish live GUI sensor truthfulness or independence, measured capture/transport/privacy/latency costs, safety, authority, causal effect, task feedback, scalability, or product readiness. It is method evidence only and does not close #6181 or the repository roadmap.
