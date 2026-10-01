# Interrupt-stack evidence-bound resume contract v1

Issue #4201. Allocation `interrupt-stack-resume-4201-20260923-01`.

H/T/D/C/U and the 96-state denominator are governed by Issue #4201. This directory freezes the exact finite-contract implementation. Construction uses only hand-authored test rows; `corpus.py` is not invoked until source freeze preparation. Formal execution is one `run.py` invocation over the frozen `CORPUS.json`, followed by the independent raw audit and copied-evidence controls. No GUI/input/model/provider/network operations.
