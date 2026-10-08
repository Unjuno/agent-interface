# Issue #6155 — route-contrast covariance T0

This is a fresh successor to the host-only T0c results on [Issue #6155](https://github.com/Unjuno/agent-interface/issues/6155). It tests the issue's open eligibility question: high per-arm `Y`/`X` correlation can be caused by shared task difficulty even when cheap and expensive **candidate-minus-baseline differences** are unrelated.

The frozen simulator has one shared-level-only negative control and signed predictive-difference controls. Candidate and Y-only comparator include the same total pilot-plus-scored cost; an independent auditor reconstructs all estimates and the decision from retained raw JSONL. Full H/T/D/C/U, source hashes, costs, run order, and gates are in [PLAN.md](PLAN.md) and [FREEZE.md](FREEZE.md).

## Result

Formal candidate ran once in a pinned network-disabled CPU-limited OrbStack container and exited 0 with 2,700 raw block records. A separate raw-only auditor container reconstructed all 9 groups and 2,700 rows, then exited 1 with `FAIL_METHOD_GATE`: the shared-level-only negative control correctly showed no resolved gain and the negative-difference control passed, but the positive-difference control's 21.08% point MSE reduction was not separated from zero by the preregistered family-wise interval. This is a method-gate failure / unresolved positive arm, not evidence that real GUI outcomes are predictable or unpredictable. See [REPORT.md](REPORT.md) and the immutable run package under [runs/](runs/MULTIFIDELITY-ROUTE-CONTRAST-6155-T0-20261002-01/).

Construction tests passed 5/5 on host Python 3.14.5 (`python3 test_method.py -v` from this directory); `py_compile` also passed. The formal container image was `python:3.12-slim` linux/arm64 at the pinned digest. Existing containers were left untouched. The original 128,461,928-byte JSONL is retained losslessly as gzip; decompression reproduces its recorded SHA-256 exactly.

The formal allocation is consumed; candidate/auditor retries are prohibited. The recorded outcome, artifacts, and gates will be published through a reviewable PR with latest-main local CI.
