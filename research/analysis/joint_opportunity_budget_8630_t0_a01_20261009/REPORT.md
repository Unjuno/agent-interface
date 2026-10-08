# Issue #8630 T0 A01 — joint observation/action/recovery budget

**Disposition: FAIL_METHOD (frozen policy-selection gate).** The candidate and raw-only enumerator each ran exactly once. The candidate matched the enumerated values, but it selected observation in the weak-signal case (0.755 with observe+recover versus 0.750 without observation and with recovery). The frozen decision required it to skip observation there. The result is retained as-is; there is no retry or post-hoc horizon change.

The informative case selected observation and recovery, scoring 0.950 versus 0.775 for fixed-action plus recovery. This is a synthetic exact-model result only. It illustrates that the preregistered “weak signal should be skipped” expectation was not true for the selected numbers, so this allocation does not pass its method gate. Mandatory verification is modeled as a required terminal opportunity in every scored schedule; the fixture does not establish any real safety or verification behavior.

Commands, each issued once from this directory:

```text
python3 candidate.py > candidate_raw.json
python3 audit.py > auditor_raw.json
```

The independent outputs enumerate four feasible observation/recovery combinations per case (8 total). A reconciliation assertion confirmed the candidate winner/value matched the auditor's enumerated maximum for the informative case, then failed the frozen weak-signal selection assertion. No candidate or auditor was rerun after that failure.

**Scope and uncertainty:** finite synthetic probabilities, exact hidden-type observation, unit opportunity costs, independent 0.5 recovery success, and only two type/action matrices. No calibrated GUI hazards, runtime behavior, model behavior, safety rate, latency, token benefit, or product effect is measured. The case does not show that joint budgeting is generally superior; it shows the frozen expected policy contrast was misspecified for one fixture.
