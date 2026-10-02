# Issue #6380 T0 — retained method-construction failure

**Disposition:** `FAIL_METHOD_CONSTRUCTION_MISMATCH`
**Allocation:** `issue6380-constraint-elicitation-t0-20261002-01`

The single frozen candidate invocation emitted 32 policy/vignette rows and exited 0. The independent auditor ran once in a network-disabled container and exited 1. Generic responses were tagged `ANSWERED`, but the candidate contract builder only retained `CONFIRMED_FORBIDDEN` responses. As a result, the generic-policy row lost the scripted hidden clause and failed the predeclared exact semantic comparison. This invalidates the policy comparison. No method pass or comparative utility claim is made.

The one-candidate and one-auditor caps are consumed. No source correction, replay, or replacement case was performed. Full raw candidate, frozen source, hashes, and failure details are retained in [`research/analysis/constraint_elicitation_6380_t0_v1/`](../analysis/constraint_elicitation_6380_t0_v1/); prior #12/#5951/#5749 evidence remains untouched. See [Issue #6380](https://github.com/Unjuno/agent-interface/issues/6380) for preregistration and failure notification.
