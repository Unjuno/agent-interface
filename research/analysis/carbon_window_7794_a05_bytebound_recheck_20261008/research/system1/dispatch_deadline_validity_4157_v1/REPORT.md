# Issue #4171 result

**Decision: PASS_DISPATCH_DEADLINE_VALIDITY_SCOPED**

24/24 frozen cases completed in the first formal allocation. All proposals were ready before the 120 ms task deadline and inside the independent 400 ms freshness/lease window. The proposal-ready-only comparator admitted all six deliberately delayed long-queue cases; the separate application process observed those effects after the task deadline. The pre-dispatch candidate refused all six long-queue cases with zero effect, while preserving all twelve on-time cases across both policies.

## H/T/D/C/U

- H: proposal-ready validity alone does not preserve a task deadline across queue delay; a fresh pre-dispatch deadline check does for this fixture.
- T: two policies x four schedules x three repetitions, 24 fresh app processes, CLOCK_MONOTONIC, deadline120ms/freshness400ms.
- D: audit rows24/errors[]; candidate late admissions0; on-time candidate refusals0; all nine corruption controls reject.
- C: injected queue delay is the treatment; dispatch validity is not application-effect completion validity.
- U: no model, GUI, production authority, hard-real-time, token/latency-benefit, or natural-rate claim.

## Construction

- construction-01 retained harness STOP/HOLD: candidate no-dispatch EOF produced app exit2.
- construction-02 changed only no-dispatch termination semantics to exit0 and passed excluded8/8.

## Integration handoff

Where task semantics include an absolute decision deadline, validate it at the last practical dispatch/apply boundary rather than only at proposal-ready time. Do not add a new universal deadline when existing lease/currentness already covers the same predicate.
