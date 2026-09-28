# H / T / D / C / U — #5215 audit-integrity successor

## Question and lineage
Successor audit-only validation for Issue #5215 and merged PR #5216. The original probe, frozen plan, and reported scientific outcome remain immutable. Current main contains an auditor that tolerates missing or malformed required negative fields, labels evidence by booleans rather than recomputing timestamp inequalities, and conflicts with its own frozen plan on effect-at-end semantics. This allocation tests the auditor boundary against the exact published raw record; it does not repeat the kernel experiment.

## H
A strict source-free auditor requiring an exact schema and recomputing all declared temporal relations from integer timestamps will reject every missing, null, wrong-type, unexpected-key, or internally inconsistent mutation of the retained record, while accepting only the original record under its explicitly reconciled expectations.

## T
Current-main CPU-only audit-invariance experiment. Input is the exact public `probe-output.json` from #5216 (Git blob d3964da3cbf6524c8193b5a59ed16bdb3611772f; nine booleans). The frozen #5216 PLAN lists nine cases and their intended classifications, but conflicts at effect_at_700; it also fixes release at 800 while testing execution end 999/1000/1001. Therefore the historical PASS cannot be upgraded by silently choosing one interpretation. The successor explicitly separates:
1. auditor structural integrity controls, and
2. plan/probe consistency checks that must HOLD where the old plan is contradictory.
The standalone standard-library implementation receives a JSON record plus a separately specified timestamp table. It imports no kernel, old auditor, old probe, or classifier. Fixed controls: clean boolean record; each missing temporal-negative field; null and string replacements; unexpected key; boolean replaced with integer; accepted-case result contradicting timestamp; release before execution end; plan classification conflict; clean identity-negative control. Each mutation starts from the same retained record. No model/GPU/CUDA/Docker/GUI/input/network or runtime change.

## D
`PASS_AUDIT_MUTATION_RESISTANCE_SCOPED` requires: exact required key set; exact booleans; explicit timestamp table; computed inequalities; every directed malformed/missing/inconsistent mutation rejected; and the original record classified as `HOLD_LEGACY_PLAN_CONFLICT` until its plan ambiguity is resolved. Any unexpected acceptance or clean-control rejection is `FAIL_AUDITOR_CONTROL`. No runtime adoption follows.

## C
The only changed variable in each mutation is the named field or relation. Independent expected results are encoded as frozen literal test vectors and integer inequalities. Tests call the audit function and do not import the implementation's expected-case table. The historical raw record is read-only.

## U
One retained synthetic record and one host Python implementation. Does not repeat execution against runtime kernel, establish real clock-domain comparability, prove OS lease enforcement or application effects, or authorize runtime changes. The old experiment remains scientifically scoped and its legacy audit claim remains under review.

## Evidence
See adjacent `audit_integrity.py`, `test_audit_integrity.py`, and `result.json`.