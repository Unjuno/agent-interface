# T0S6 decision-gate audit successor

Allocation `INTENT-SLOT-6081-T0S6-20261002-GATE-AUDIT-01` is a fresh decision-only audit of S4's immutable 80-row raw, after S5 independently reconstructed that raw exactly and its own output exposed a gate implementation discrepancy. S4 and S5 records remain unchanged. No candidate or earlier auditor is rerun.

S6 tests the exact preregistered D gate in S4 `PLAN.md`: A/B stationary equivalence; at least three eligible nonrepresentable wins; no **increased** prefix-envelope violation in C relative to the shared nearest-action baseline; no candidate switch/release/illegal-action issue; and exact/zero/refusal controls. Unsafe baselines are reported, not silently treated as proof that C is unsafe; only cases with both C and baseline scheduled and prefix-safe enter the approximation win denominator. All comparisons are exact rational.

S6 reads the S4 raw and S5 reconstruction receipt read-only, verifies their frozen hashes and S5's 80-row `EXACT_MATCH`, then independently recomputes the policy sequences/metrics needed for the decision. Formal budget: one S6 decision auditor, zero candidate, zero retries. Its result is scoped to the synthetic fixture.
