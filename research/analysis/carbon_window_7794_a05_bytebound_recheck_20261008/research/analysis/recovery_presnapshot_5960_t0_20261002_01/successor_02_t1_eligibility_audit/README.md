# T1 retained-cohort eligibility audit — Issue #5960

Read-only bounded inventory of nearby retained records; no old allocation is rerun, repaired or relabeled. The gate requires case-level pre/post evidence, a source clock, an independently grounded causal label, an eligible non-immediate-hazard/safe-slack failure, and a result about diagnosis/reproducer utility after recovery.

Run `python -m unittest -v test_eligibility.py`, then once run `python audit_eligibility.py`. `eligibility_inputs.json` is the frozen extraction of each cited artifact's scope and limitations; `FREEZE.json` pins its main commit and source Git blobs. The result can only establish a bounded HOLD/PASS for these cited candidates, not a universal absence claim.
