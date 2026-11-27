# Reuse horizon all-attempt accounting — 2026-11-04

## Question
Does the reuse-horizon validator preserve complete provider-attempt costs when an arm-C warm task incurs a model attempt that does not generate a new semantic plan?

## Change
Schema `agent-interface/reuse-horizon-comparison-v2` separates plan lineage from accounting. Each arm-C trace row now carries an ordered `attempt_dispositions` entry for every model attempt in its ledger. The list must exactly match ledger event order; every disposition is finite and checked against the attempt status. `plan_generation_attempt_ids` must exactly equal the attempts tagged `plan_generation`. Stale responses, fallback, other completed non-plan responses, abstention, failure, timeout, cancellation, refusal, and malformed responses remain distinct dispositions. Missing, duplicate, out-of-order, unknown, or status-inconsistent classifications are rejected.

Cumulative token and elapsed totals continue to come from the full validated task ledger, so every model attempt is charged. Incomplete usage makes subsequent cumulative token totals unknown. Warm and post-repair warm rows still reject plan generation; extra non-generation calls remain visible in `plan_trace`.

## Test evidence
Pinned local image `agent-interface-xvfb-mcp:late-input-r19` (`sha256:bd191d30ea94871a1d3ca717252cd07a276e8ef7d1bcb4a130b63935ce075425`), Docker Engine 29.8.1. Offline container limits: 2 CPU, 4 GiB memory and swap, 256 PIDs; networking disabled; source mounted read-only; packet writable. No provider generations or GUI actions.

`test_comparison_measurement_v1` passed 14/14 in normal mode and 14/14 under `python3 -O`; exit status 0 for both. The regression case adds a completed stale warm response with 1 input and 1 output token and 10 ns of extra full-lifecycle time. C cumulative totals become 10, 12, 22, 22 tokens and 30, 70, 100, 130 ns. Tests also confirm missing classification, false plan-generation lineage, status mismatch, and unavailable token usage are rejected or propagated conservatively as appropriate.

The first iteration exposed a fixture-only observation timestamp mismatch after extending provider wait; the retained successful run uses the corrected observation capture time. The initial attempt's raw stdout was not written to this packet; final normal and optimized logs are preserved here.

## Scope limits
This is synthetic validator evidence only. It does not establish live provider usage, real Calc behavior, WSLc, MAP01, or end-to-end efficiency. It does not change Issue #57's live comparison gates.