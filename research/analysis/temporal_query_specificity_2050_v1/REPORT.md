# Temporal query specificity at the model boundary (#2050)

## Disposition

**HOLD_PRE_MODEL_COST_BOUNDARY**

A ten-case fixed temporal-task family was evaluated once. The arms were UNIVERSAL_FIXED_HISTORY, CLASS_ONLY_QUERY, CLASS_PLUS_ANCHOR_QUERY, and WRONG_CLASS_OR_ANCHOR. The local evaluator verified deterministic query construction and canonical JSON serialization.

Observed totals:
- UNIVERSAL_FIXED_HISTORY: 5,359 bytes / 100 history items
- CLASS_ONLY_QUERY: 2,099 bytes / 30 history items
- CLASS_PLUS_ANCHOR_QUERY: 1,709 bytes / 20 history items
- WRONG_CLASS_OR_ANCHOR: 1,230 bytes / 10 history items

All class/anchor inputs, including unknown and shifted values, remain serialized rather than silently replaced. Serialization oracle and unknown-input retention passed. Digest: `a4ecfd27080cba10ca7a55d6fe844723c9eef65e814d1629b7593f8322eb6d3c`.

## Execution boundary

A container invocation was attempted with `python:3.12-slim`, but remained queued behind a concurrent MAP01 Docker workload and was not used as scientific evidence. It was not cancelled or allowed to alter the other workload. The same script was run locally only as a fallback construction/serialization check. Formal container count: 0; local check: 1; model/GUI/task-input: 0.

These measurements are not model-boundary cost, end-to-end latency, temporal correctness, or task utility. They omit capture, transport, provider/model tokenization, and model response behavior. The next rung must use the frozen cases with real capture/packaging/model measurements before any policy promotion.
