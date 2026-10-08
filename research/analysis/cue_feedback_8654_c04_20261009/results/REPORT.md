# Issue #8654 C04 — result

Disposition: PASS_METHOD_SCOPED

Source commit: 6eda1ccce720be86601fbcdb3da30a20067c605d
Workflow run: https://github.com/Unjuno/agent-interface/actions/runs/37809539021
Runner: ubuntu24 / Python 3.12.10

Integrity: PASS_METHOD_SCOPED
Study outcome: COUNTEREXAMPLE_TO_SUPPORT_SUFFICIENCY_SCOPED
Stable fully supported wrong rows: 66
Stable fully supported wrong probability mass: 7.984352827457297e-06

| Regime | Complete-support mass | Correct mass | Error mass | Accuracy among supported |
|---|---:|---:|---:|---:|
| STABLE | 0.9800552604494894 | 0.980047276096662 | 7.984352827457297e-06 | 0.9999918531605823 |
| REVERSAL | 0.9800552604494894 | 0.9800552604494894 | 0.0 | 1.0 |
| GLOBAL_SHIFT | 0.9800552604494894 | 0.9800552604494894 | 0.0 | 1.0 |

Raw JSONL SHA-256: 9acfccce471afdd664b59d85b26cbba2a726dd1c8214497098718c14d29b988d (268941 bytes).

## Scope

This is an exact deterministic finite-sample method result only. It does not test stochastic rewards, propensity misspecification, sequential learning, GUI behavior, user outcomes, runtime benefit, or safety. The C01 raw-custody STOP remains unchanged.

The pre-audit raw artifact must have succeeded before an auditor invocation is counted. No retry was authorized or performed.
