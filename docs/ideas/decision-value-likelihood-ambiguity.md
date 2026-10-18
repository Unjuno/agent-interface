# Decision-value observation selection over likelihood ambiguity sets

- **Status:** Finite method result passed; deployment likelihood uncertainty remains unmodeled.
- **Source:** Issue [#7955](https://github.com/Unjuno/agent-interface/issues/7955), successor to [#7934](https://github.com/Unjuno/agent-interface/issues/7934).
- **Idea:** Compare decision-rule-specific value of information with envelopes over a set of plausible likelihood models, keeping admissibility and hard constraints fixed.
- **Outcome:** A01 `PASS_METHOD_SCOPED` across six finite cases; the independent enumerator reconstructed 22 likelihood models, 41 value rows, and 22 evaluation truths. It captured a rank reversal and returned `UNKNOWN_NO_ADMISSIBLE_CHECK` when all checks were inadmissible. This is an authored finite model, not a calibrated deployment credal set, live GUI policy, or safety result. Evidence remains in open Draft [PR #7984](https://github.com/Unjuno/agent-interface/pull/7984).
