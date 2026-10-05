# Carryover-aware optional adaptation estimator — Issue #7834

This package contains two source-frozen synthetic construction allocations. It does not use GUI, model, user, GPU, runtime, or action data.

| Allocation | Scoped outcome | Candidate / audit | Runtime |
|---|---|---:|---|
| A01 | PASS_METHOD_SCOPED_A01; 30 rows; IPW/oracle proximal 1.0; executed-only 4.0; distal -2.0; 10/10 mutations rejected. A01 omitted the no-carryover comparator and did not finish the Issue T0. | 1 / 1, zero retries | Host V8 memory |
| A02 | PASS_METHOD_SCOPED; 30 rows; IPW/oracle 1.0; executed-only 4.0; unweighted/no-carryover 1.5; no-history IPW 1.0; distal -2.0; 11/11 mutations rejected. | 1 / 1, zero retries | Host V8 memory |

The exact outcomes, freezes, source, fixtures and raw JSON streams are in the allocation subdirectories. See [Issue #7834](https://github.com/Unjuno/agent-interface/issues/7834), freeze comments #5986020822 and #5986063966, and outcome comments #5986033700 and #5986082966.

## Interpretation and limits

Within the authored finite distribution, known-current-propensity assignment weighting recovers the enumerated marginal proximal effect; executed-only and unweighted/no-history contrasts do not. A pooled IPW estimate without an explicit history model equals the oracle in A02, so history adjustment adds no accuracy for this particular marginal estimand and fixture.

This is construction/method evidence only. It is not an empirical micro-randomized trial, a causal effect in a real interface, or evidence of user/task benefit. Two fixed latent session types, deterministic adherence, complete proximal windows, known propensities, and bounded carryover do not represent actual users or application behavior.

WSLc could not provide an inspectable inventory because the host C: volume was full. Per the frozen records, both allocations therefore used the in-memory host V8 runtime; no local artifacts were written. This is an explicit runtime deviation from the preferred container route.
