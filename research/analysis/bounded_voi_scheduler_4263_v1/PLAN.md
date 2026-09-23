# #4263 bounded VoI scheduler v1 — frozen plan

Allocation: `bounded-voi-scheduler-4263-20260923-01`.
Base main: `affe58482c57317f135b15b65f8e94beb8fe42ac`.

## H
After a shared hard feasibility/support gate, a preregistered sequential value-of-information selector can preserve the same correctness/YIELD contract while reducing expected evidence/computation cost relative to FIXED_CASCADE and CHEAPEST_FIRST on a frozen held-out finite distribution.

## T
Standard-library exact finite table. Four actions: CHEAP(cost1, latency1), ROI(3,3), SPECIALIST(5,6), RICH(12,10). Wrong-decision loss100, required-YIELD loss8, deadline miss diagnostic30. Development weights and observation table are frozen in `experiment.py`; evaluation is separate and contains easy, ROI-useful, specialist-useful, deadline-pruned, ambiguous, and support-shift blocks. All policies share the same support-violation=>YIELD rule. FROZEN_VOI_POLICY uses development likelihoods only and a one-step expected-risk-reduction-per-cost selector after the mandatory CHEAP probe. No online update or formal tuning.

Construction-01 is retained: the first draft allowed an out-of-development support observation to fall through to an arbitrary terminal decision, causing 5% weighted error. Before freeze only, this was repaired by making support violation a common YIELD contract and marking the held-out support-shift cells as required-YIELD. Construction-02 then passed. No formal row existed before this repair.

Formal: exactly one invocation producing the full held-out evaluation table for all three policies. No randomness, retries, replacement, pooling or post-result source/gate tuning.

## D
`PASS_BOUNDED_VOI_SCHEDULER_SCOPED` iff FROZEN_VOI_POLICY has zero weighted incorrect decisions, zero required-YIELD violations, deadline-miss rate no greater than either baseline, and strictly lower weighted total evidence cost than both baselines. `FAIL_VOI_CORRECTNESS_REGRESSION` on any correctness/YIELD regression. `FAIL_DEADLINE_MISS_INCREASE` on increased deadline misses. `HOLD_FIXED_CASCADE_SUFFICIENT` if correctness is preserved but cost is not strictly better than both. `HOLD_ESTIMATES_NOT_TRANSFERABLE` if support/shift remains safe but the frozen estimate policy fails the primary endpoint. Missing/floating value model before formal => STOP.

## C
This compares sequential policies only. Parallel starts may dominate. The finite synthetic table makes likelihoods exact on development support; real semantic/model costs can drift. Required YIELD under unseen support is a contract choice, not evidence that every real distribution shift should yield.

## U
No GUI/input/model/provider/network call. No authority, freshness, safety or forbidden-effect constraint may be overridden by VoI. No real latency/token/provider-cost or production/generalization claim.
