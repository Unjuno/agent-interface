# Issue #4171 preformal plan

Allocation: dispatch-deadline-4171-20260923-01

## H
Proposal-ready validity is insufficient if queue/admission delay makes the actual dispatch late. Rechecking the same 120 ms task deadline immediately before dispatch should reject the late dispatches while preserving on-time cases.

## T
Two policies: PROPOSAL_READY_DEADLINE and PRE_DISPATCH_DEADLINE. Four schedules: EARLY_SHORT 20+20 ms, NEAR_SHORT 90+10 ms, NEAR_LONG 90+60 ms, EARLY_LONG 20+140 ms. Three repetitions per cell = 24 fresh application processes. Separate application subprocess records receive/effect time in the same CLOCK_MONOTONIC domain. Task deadline 120 ms; independent freshness/lease control 400 ms. No model, GUI, OS task input, or experiment network.

## D
PASS_DISPATCH_DEADLINE_VALIDITY_SCOPED requires all24 rows; proposal-ready <=120 ms; both policies admit the two short schedules and application effect is <=120 ms; baseline admits all six long-schedule cases and their application effects are >120 ms; candidate refuses all six long-schedule cases with zero effect; authority is always false; all app exits0; raw audit errors=[]; >=8 semantic mutations reject.

## C
Queue delay is deliberate. Dispatch-validity is not effect-completion validity. The 120 ms deadline is authored for this fixture, not universal.

## U
No model/task utility, GUI, production authority, hard-real-time guarantee, clock translation, token/latency benefit, or natural-rate claim.

Construction-01 is retained FAIL/HOLD due to harness treating candidate no-dispatch EOF as app exit2. Construction-02 changes only that app no-dispatch termination contract and passes8/8; both are excluded from formal.
