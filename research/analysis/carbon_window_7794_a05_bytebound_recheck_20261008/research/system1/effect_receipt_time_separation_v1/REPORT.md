# Issue #4231 result

**Decision: PASS_EFFECT_RECEIPT_TIME_SEPARATION_SCOPED**

The owner commit time and terminal receipt-delivery time are observably distinct in the frozen fixture. All 36 first-outcome cases completed in one formal invocation.

- Receipt-arrival policy: the three ON_TIME_LATE_RECEIPT effects committed at about 60.5–60.6 ms but were classified LATE because receipts arrived around 170.9 ms.
- Owner-commit policy: the same schedule was ON_TIME 3/3 from identity-bound owner journal evidence.
- Actual late commits around 150.6 ms were LATE 3/3 under the owner-commit policy.
- Unverified commit fields remained UNKNOWN; no authority/retry authority was granted.
- NO_COMMIT produced NO_EFFECT in all policies.

Raw-only audit: 36 rows, errors=[]. All 12 semantic/provenance corruption controls reject. Frozen source hashes remained unchanged. Formal reruns/replacements/tuning: 0/0/0.

## H/T/D/C/U

H: receipt arrival is delivery timing, not effect timing. An identity-bound owner commit timestamp preserves on-time effect semantics across delayed receipt delivery.

T: separate owner process, fsynced effect bytes and append-only journal, common CLOCK_MONOTONIC domain, task deadline120 ms; 3 policies x4 schedules x3 repetitions.

D: every frozen decision gate passed.

C: cooperative same-clock owner; fsync return is a fixture commit point, not power-loss durability. Directed delays are not natural latency distributions.

U: no distributed clock/authentication, model/GUI/task utility, external service, hard-real-time, token/latency-benefit, or product claim.

Integration handoff: keep effect commit time and receipt-delivery time as separate fields. A late receipt must not retroactively relabel a proven on-time effect, and an unverified claimed commit timestamp must not become authority.
