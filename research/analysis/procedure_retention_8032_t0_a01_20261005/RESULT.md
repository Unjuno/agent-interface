# T0 A01 result — Issue #8032

**Disposition: `METHOD_PASS_SCOPED` for authored protocol/scoring construction; `HOLD_T1_FEASIBILITY_AND_REVIEW`.** No participant effect was measured.

The candidate validator accepted the frozen three-arm, six-opportunity schedule and rejected opportunity/evidence mismatch, incomplete training-packet count, invalid retrieval timing, answer-key leakage and transfer-task leakage. The synthetic scoring packet has six authored counterexamples: complete core, wrong order, final-state mismatch, critical wrong target, missing delayed outcome, and complete held-out transfer. Candidate and separately implemented raw-only auditor matched all six expected rows. Takeover-state correctness and vigilance hit/miss/false-alarm/correct-rejection scores are independently reconstructed and remain separate from delayed retention.

Normal and optimized host-CPython tests passed 18/18 each. A separate process using only `audit.py` reported plan valid and reconstructed all six retention statuses: complete, incomplete, incomplete, critical_error, missing, complete. JSON parsing passed 2/2. WSLc returned `E_FAIL` before the final candidate test suite could start; no final WSLc PASS is claimed. See `RUN.md` and `FAILURES.md`.

The illustrative power grid implies 318 recruits at assumed d=.50 or 648 at d=.35 for four contrasts and 15% attrition. The per-person protocol is estimated at 20 + 10 minutes, but total recruitment, exact ordinal-score power, and participant availability remain unresolved. Thus the T1 feasibility decision is HOLD; it requires independent review, ethics/privacy approval, consent, recruitment capacity, exact power analysis and fresh authorization. T0 is not an ethics approval or a human study.

This is method construction on an authored fixture only. It is not evidence of skill decay, retrieval benefit, transfer in people, GUI safety, takeover readiness, vigilance, or an Agent Interface product effect.
