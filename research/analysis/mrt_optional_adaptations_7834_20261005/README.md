# Carryover-aware optional adaptation estimator — Issue #7834

This package contains three source-frozen synthetic construction allocations. A01 and A02 ran in host V8 memory; A03 is a separate exact-source replay in a network-disabled WSLc Node container. No allocation uses GUI, model, user, or action data.

| Allocation | Scoped outcome | Candidate / audit | Runtime |
|---|---|---:|---|
| A01 | PASS_METHOD_SCOPED_A01; 30 rows; IPW/oracle proximal 1.0; executed-only 4.0; distal -2.0; 10/10 mutations rejected. A01 omitted the no-carryover comparator and did not finish the Issue T0. | 1 / 1, zero retries | Host V8 memory |
| A02 | PASS_METHOD_SCOPED; 30 rows; IPW/oracle 1.0; executed-only 4.0; unweighted/no-carryover 1.5; no-history IPW 1.0; distal -2.0; 11/11 mutations rejected. | 1 / 1, zero retries | Host V8 memory |
| A03 | PASS_METHOD_SCOPED_A03; exact 30-row replay; proximal IPW/oracle 1.0; executed-only 4.0; unweighted/no-carryover 1.5; no-history IPW 1.0; distal -2.0; 11/11 mutations rejected. | 1 / 1, zero retries | WSLc 3.0.1.0, pinned Node 22 image |

The exact outcomes, freezes, source, fixtures and raw JSON streams are in the allocation subdirectories. See [Issue #7834](https://github.com/Unjuno/agent-interface/issues/7834), freezes #5986020822, #5986063966 and #5986196185, and outcomes #5986033700, #5986082966 and 5986252610.

## Interpretation and limits

Within the authored finite distribution, known-current-propensity assignment weighting recovers the enumerated marginal proximal effect; executed-only and unweighted/no-carryover contrasts do not. A pooled IPW estimate without an explicit history model equals the oracle in A02/A03, so explicit history adjustment adds no accuracy for this marginal estimand and fixture.

This is construction/method evidence only. It is not an empirical micro-randomized trial, a causal effect in a real interface, or evidence of user/task benefit. Two fixed latent session types, deterministic adherence, complete proximal windows, known propensities, and bounded carryover do not represent actual users or application behavior.

A01/A02 were frozen before WSLc inventory became available and used host V8; their historical runtime deviations remain unchanged. A03 separately confirms this source-bound finite construction in WSLc; it does not re-label the earlier runs, demonstrate a GPU use case, or establish container performance, memory enforcement, or broader runtime parity.
