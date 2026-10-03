# A01 analytical contract (prospective)

Allocation: #5504 comment 5968198522; proposal comment 5937946951.
This is a finite expressibility model, not the production Verification IR.
No old allocation, runtime, GUI, GPU, model, or container is executed.

The ordered predicates are `authority`, `current`, `effect_safe`,
`dependencies_acyclic`, `reversible`. Every Boolean valuation appears exactly
once. Case IDs `case_000` through `case_031` encode a five-bit binary number,
most significant bit first; the ID is bookkeeping, not an observable predicate.
The independently declared oracle is PASS iff all five predicates are true.
Labels in real applications are not established by this synthetic oracle.

The restricted vocabulary omits `reversible`. The complete control includes
all five predicates, predeclared here, not invented after inspecting output.

JSON output has exactly these top-level keys:

- `schema`: string `verification-ir-alias-boundary-v1`.
- `predicates`: the five ordered strings above.
- `oracle`: string `PASS iff all five predicates are true`.
- `rows`: ordered 32 records, each exactly `{case_id, concrete, required}`.
  Concrete is a five-element list of JSON booleans; required is PASS or FAIL.
- `restricted` and `complete`: each exactly `{vocabulary, status,
  observable_class_count, conflicting_classes, decisions}`.
  Vocabulary is an ordered list of predicate names. Status is
  `ONTOLOGY_INSUFFICIENT` or `EXPRESSIBLE`. Each conflicting class has exactly
  `{visible, members, required}`: a Boolean visible vector, sorted member IDs,
  and sorted distinct required labels. No case ID is an input to a decision.
  Decisions is null when there is any conflicting class, otherwise an ordered
  list of `{visible, required}`, sorted lexicographically by Boolean vector.

Frozen predictions: restricted 16 observable classes, one conflicting class
with visible `[true,true,true,true]`, members `case_030`, `case_031`, required
`FAIL`, `PASS`, null decisions; complete 32 singleton classes, zero conflicts,
32 exact decisions (31 FAIL, 1 PASS). No measured speed or learned convergence.

Independent auditor reads raw output bytes; it does not import or execute the
producer. It reconstructs the model with bit masks, checks exact types/schema,
every valuation/label, both controls and retained witness membership. JSON
duplicate object keys and nonstandard numeric constants must be rejected.
Error => FAIL, exit 1; valid => PASS, exit 0. Audit JSON has `status`, `errors`,
`rows_checked`, `observable_classes_restricted`, `conflicting_classes`,
`complete_decisions`, `input_sha256`. Host formal modelchecker and independent
read-only audit run once each after source freeze; first output is retained.

Construction tests/corruptions are not formal measurements. An independent
auditor's constructed fixture is not another formal producer output. A failed
frozen formal execution closes A01, with no repair/rerun in the allocation.
