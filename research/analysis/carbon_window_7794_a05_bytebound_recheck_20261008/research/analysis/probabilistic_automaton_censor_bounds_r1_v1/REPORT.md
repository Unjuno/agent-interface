# #1892 Censor-bound partial identification result

Decision: **PASS_PROBABILISTIC_AUTOMATON_CENSOR_BOUND_PARTIAL_ID_SCOPED**

Given observed completion rates x=p*a and y=(1-p)*b and positive censor/completion bounds a_L<=a<=a_U and b_L<=b<=b_U, the sharp transition-probability interval is:

L = max(0, x/a_U, 1-y/b_L)
U = min(1, x/a_L, 1-y/b_U).

The formal exact-Fraction corpus contains 3,600 compatible rows.

- candidate/oracle interval mismatch: 0
- true p excluded: 0
- empty compatible intervals: 0
- interval outside #1890 no-mechanism bound [x,1-y]: 0
- exact point-bound rows: 144; failures to identify p exactly: 0
- strict tightening versus [x,1-y]: 3,175
- valid non-point partial intervals: 1,656
- both A/B bounds strictly tighter than A-only: 1,714
- both-bounds wider than A-only: 0
- endpoint sharpness checks: 7,200; failures: 0
- completion-only wrong point estimates: 2,664
- midpoint plug-in wrong point estimates: 3,078

One directed example has x=1/10, y=9/20, a in [1/4,1], b in [1/2,3/4], yielding the sharp p interval [1/10,2/5]. It is narrower than the no-mechanism interval but is correctly not collapsed to an unjustified point.

Interpretation for #1658: calibrated censor information should propagate as a transition-probability identified set unless the censor mechanism is known tightly enough to point-identify the transition. A bounded interval is evidence, not failure. Midpoint substitution and completion-only normalization both create unsupported point claims on many compatible rows.

Source-first readback matched3/3 before formal. Independent audit reproduced all counters exactly. Formal invocation1; reruns/replacements/tuning0.

Scope: deterministic nuisance-parameter bounds, not statistical confidence intervals. No live GUI estimate, prediction quality, action authority, latency or product claim.
