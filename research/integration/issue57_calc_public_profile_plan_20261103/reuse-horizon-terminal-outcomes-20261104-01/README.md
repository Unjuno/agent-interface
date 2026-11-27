# Reuse horizon terminal outcomes and bounded retries — 2026-11-04

## Question
Can the reuse-horizon report retain complete attempt costs when cold plan generation or dependency repair fails, without presenting the partial sequence as a successful efficiency comparison?

## Schema v3 behavior
- The predeclared horizon records a maximum of 16 C model attempts per task; each comparison must declare its cap (tests use 3, retry test uses 2).
- Each observed block still has matched A/B/C runs. The trace explicitly marks its plan as available or unavailable and retains an exhaustive ordered disposition for every C model attempt.
- A failure, timeout, abstention, stale response or fallback attempt before one successful plan generation can be followed by a bounded successful generation in the same cold/repair task. At most one generated plan is retained per C task.
- If cold generation ends with no plan, the sequence terminates after block 1. If repair ends with no plan, it terminates at the declared repair block. Partial horizons retain A/B/C scores, token and elapsed totals, but all break-even indices are null. The report marks `horizon_complete=false` and a typed `horizon_outcome`.
- If a plan exists but its independently scored task fails, the block remains in the record and correctness-qualified break-even reflects the successful prefix rather than rejecting the whole dataset.
- Unknown token usage propagates as null; elapsed time for all observed attempts remains cumulative.

## Test evidence
Pinned local image `agent-interface-xvfb-mcp:late-input-r19` (`sha256:bd191d30ea94871a1d3ca717252cd07a276e8ef7d1bcb4a130b63935ce075425`), Docker Engine 29.8.1. Offline container limits: 2 CPU, 4 GiB memory and swap, 256 PIDs; network disabled; source read-only; packet writable. No provider generations or GUI actions.

`test_comparison_measurement_v1` passed 17/17 in normal and 17/17 in optimized (`python3 -O`) mode, both exit 0. The cold retry case charges a failed attempt plus the successful generation: C cumulative token totals are 12, 12, 22, 22 and elapsed time is 40, 70, 100, 130 ns. A terminal cold abstention retains its one-block costs but reports no break-even. A terminal repair timeout with unavailable usage retains cumulative C totals `[10, 10, null]`, elapsed `[30, 60, 90]`, and no break-even.

The initial v3 run exposed implementation/test mismatches: the trace length was still tied to the target horizon rather than its observed prefix; the retry fixture did not extend the full measured lifecycle; and one correctness-prefix assertion expected the wrong result. Those were corrected before the final run. The initial failure stdout was not retained as raw; the final normal and optimized logs are preserved here.

## Scope limits
This validates synthetic offline records, not live provider usage or a production recovery controller. It is not a live Calc efficiency result and does not establish WSLc, MAP01, end-to-end latency, or host crash prevention. Predeclaration is represented in the measurement record but is not cryptographically proven by this validator.