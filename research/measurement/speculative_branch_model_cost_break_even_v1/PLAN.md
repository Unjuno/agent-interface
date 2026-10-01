# SPECULATIVE-BRANCH-MODEL-COST-BREAK-EVEN-20260918-001

H: The retained K2 temporal absolute latency advantage over K1 can be converted into a strict residual budget for unknown incremental model-side authoring cost after charging measured local second-branch preparation cost.
T: Pin exact #1127/#1153/#1174 result blobs. Recompute raw gap = K1 temporal mean - K2 temporal mean. Subtract #1174 mean/p50/p95/p99 marginal local cost. Keep same-generation unknown model cost separate from an observed full-call probe reference. No actual model cost is estimated.
D: PASS_MODEL_BRANCH_AUTHORING_BREAK_EVEN_LOCALIZED_SCOPED iff parent blobs/types reproduce, raw gap is 7.82655 ms, all four residual budgets are positive/exact, actual_model_incremental_cost remains null, and full-boundary reference remains noncausal.
C: Synthetic planner-gap means are not production traffic; model token count and wall do not necessarily scale linearly. An extra generation is not equivalent to a longer same generation.
U: Analytic boundary only; no model call or token-price estimate.
