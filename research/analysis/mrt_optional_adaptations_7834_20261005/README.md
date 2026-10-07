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


| A04 | PASS_METHOD_SCOPED_A04_QUALIFIED; 2,600 rows; proximal IPW/oracle 2.583333 (arm 1 vs 0) and 0.166667 (arm 2 vs 0); observation rate 0.8; distal scores U=0: 8.44375, U=1: 9.44375; 17/17 mutations rejected. Six nonidentifiability controls returned NONIDENTIFIABLE. The freeze text said “five”; see qualification #5986498125. | 1 / 1, zero retries | WSLc 3.0.1.0, pinned Node 22 image |

A04 expands the finite construction to three arms and an observation/censoring mechanism. The quoted five-control minimum was a freeze-text count error: the hash-frozen fixture contains six distinct controls, and all six were tested and returned NONIDENTIFIABLE. The original freeze and post-run qualification are both preserved; this is a qualified pass, not a rewritten preregistration. See freeze #5986448843, construction/qualification #5986498125 and outcome #5986505971.

A04 remains synthetic, method-scoped evidence. It does not establish empirical treatment effects or product benefit, and does not address GPU performance.

| A05 | FAIL_METHOD; frozen estimator and auditor halved stratum effects by dividing weighted sums by two assignment rows; reported M0=+1, M1=-0.5 instead of +2/-1; auditor shared the same denominator defect; mutation gate 6/7. Preserved, not rerun. | 1 / 1, zero retries | WSLc 3.0.1.0, pinned Node 22 |
| A06 | PASS_METHOD_SCOPED_A06; 4 rows; M0=+2, M1=-1; equal-stratum pooled +0.5; heterogeneity +3; three NONIDENTIFIABLE controls; independent oracle agrees; mutations 7/7. Fresh allocation after A05 failure. | 1 / 1, zero retries | WSLc 3.0.1.0, pinned Node 22 |

A05/A06 test moderator-specific treatment effect heterogeneity under known assignment propensities using a two-stratum finite construction. The A05 failure remains unchanged; A06 is a fresh source-frozen successor, not a relabeled result. Both are method-only synthetic evidence and do not establish moderator discovery, sampling accuracy, real-user effects, product benefit, or a GPU use case. See A05 freeze/outcome #5986630463/#5986643544 and A06 freeze #5986671820.
