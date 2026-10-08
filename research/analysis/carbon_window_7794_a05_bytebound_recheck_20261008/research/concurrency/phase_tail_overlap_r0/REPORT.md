# #1670 Report — phase-level overlap behind one serialized input actuator

**Decision: `PASS_PHASE_LEVEL_OVERLAP_SCOPED`.**

## Claim
A single global input actuator does not imply whole-intent serialization. If each independent intent has one non-preemptive input burst on the shared actuator followed by a surface-local effect/verification tail that does not use that actuator, then later input may safely overlap earlier tails. Among all such schedules, order input bursts by non-increasing tail duration.

## Proof
Let job i have input-burst duration p_i > 0 and tail q_i >= 0. Only one input burst may run at a time. Once its input burst completes at C_i, its tail runs independently and finishes at C_i + q_i. The schedule objective is M = max_i(C_i + q_i).

Take any adjacent inverted pair i then j with q_i < q_j, starting their input at time t. In the original order the two relevant finish times are t+p_i+q_i and t+p_i+p_j+q_j. Since p_j>0 and q_j>q_i, the second is the larger, so the pair contribution is t+p_i+p_j+q_j.

Swap the pair to j then i. The two finish times become t+p_j+q_j and t+p_j+p_i+q_i. The first is at most t+p_i+p_j+q_j because p_i>0. The second is also at most that original maximum because q_i<q_j. Therefore swapping an adjacent inversion never increases M.

Repeatedly remove all inversions. This terminates at an order with non-increasing q_i, and no exchange increased M. Hence a longest-tail-first order is optimal.

Whole-intent serialization waits each tail before admitting the next input, with makespan B = sum_i(p_i+q_i). The phase scheduler instead has makespan max_i(C_i+q_i), so it can be strictly smaller whenever a nonzero tail overlaps later work.

## Frozen formal
Before the one formal invocation, exact SHA-256 values were frozen:
- PLAN.md `d9378367110509406032b52924734df581ceaa7ddb48782fc0b06667b7a4ab78`
- prove.py `9fdf93fe77766aaeeb0301bf5fae519487ba583430640838c5b96b1003b502ad`
- audit.py `a812dfd90587b292e472ebfa18a34f25b534d9a0e5f7b9a40991f3889e592a9e`
- FREEZE.json `d211d632c9d7d24b352cf75bcb07cdc11bf41030f8dc42766d98798b1b129b26`

Formal budget 1; reruns 0; tuning after freeze 0.

The formal enumerated n=2..5, p_i in {1,2}, q_i in {0,1,2,3}. For every one of 37,440 job vectors it compared longest-tail-first with every permutation.

| n | cases | counterexamples | strict gain vs whole-intent serial | bounded max speedup |
|---:|---:|---:|---:|---:|
| 2 | 64 | 0 | 60 | 7/4 = 1.75x |
| 3 | 512 | 0 | 504 | 9/4 = 2.25x |
| 4 | 4,096 | 0 | 4,080 | 13/5 = 2.6x |
| 5 | 32,768 | 0 | 32,736 | 17/6 = 2.8333x |

Total: 37,440 cases, zero counterexamples, 37,380 strict improvements. The independent auditor recomputed all 37,440 cases and passed all gates.

The 17/6 maximum is only the maximum inside this bounded enumeration. It is not a production speed claim.

## Design consequence
The scheduler should not attach exclusivity to an entire intent merely because its action phase uses one global pointer/keyboard resource. Instead, each phase should declare resources separately:

- INPUT: exclusive actuator/focus resources;
- EFFECT_PENDING: no input authority unless explicitly required;
- VERIFY: surface-local observation/scorer resources;
- CLEANUP/HANDBACK: only the resources actually needed.

Then serialize conflicting phases, not unrelated waiting/verification work. This complements #1643: genuine multiple actuators are one source of concurrency, but phase decomposition can recover useful concurrency even with one actuator.

## Failure boundary
Do not apply this rule if a tail still holds keys/buttons, uses shared focus/clipboard, mutates shared state, needs a result before later input is valid, or shares a verifier/resource with another tail. Such dependencies must appear as graph edges and can force serialization.

## Next live discriminator
Use two independent X11 surfaces with one shared ordinary input actuator. Freeze two short action bursts followed by independently observable delayed effects. Compare:
1. whole-intent serial: input A -> wait/verify A -> input B -> wait/verify B;
2. phase overlap: input A -> input B while A effect is pending -> verify A/B independently;
3. negative hidden-conflict condition that must serialize.

Require exact per-surface effect scoring, no cross-surface contamination, verified neutral input state, and measured physical input/effect intervals. This tests the theorem's applicability rather than re-proving scheduling arithmetic.

## Limits
Abstract deterministic model only; known tail durations; non-preemptive input bursts; independent tails. No GUI, model, network, token, human-tempo or end-to-end product claim.
