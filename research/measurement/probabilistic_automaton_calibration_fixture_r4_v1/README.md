# Prospective probabilistic automaton calibration fixture

This is the container-independent construction/formal core for Issue #1911.
It uses only the Python standard library and emits one deterministic visible
ledger from a frozen seed. The authored dwell values are retained only inside
the fixture generator; the candidate summary consumes typed next-state labels
and completed/censored dwell observations. For this integer-valued fixture, a
censored dwell is strictly greater than the horizon, so the lower bound uses
the first unobserved value (5), while the trusted fixture maximum supplies the
upper bound.

Run:

```bash
python research/measurement/probabilistic_automaton_calibration_fixture_r4_v1/experiment.py
python research/measurement/probabilistic_automaton_calibration_fixture_r4_v1/audit.py
```

The expected scoped result is PASS when the transition population is A=600,
B=400, the candidate dwell intervals are A=[11/3,4] and B=[3,4], and the
completion-only comparator incorrectly estimates p(A)=2/3. This is calibration
mechanics only: it makes no claim about GUI distributions, prediction quality,
latency, authority, or deployment probabilities.

`audit.py` independently recomputes counts and intervals from the visible
ledger and applies four one-field corruption controls (next-state, censor
status, horizon, and episode identity). Every corruption must be rejected.
