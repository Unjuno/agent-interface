# OPERATION-TARGET-PURPOSEBUILT-CORPUS-20260918-001

BASE: `a2f4151586769a2e12d64a2db74c571d3e9f805f`
Issue: #1133
Reservation branch: `research/operation-target-purposebuilt-corpus-20260918-001`

## H
A purpose-built, predeclared decision-state fixture can generate a leakage-free operation/target corpus satisfying #1015's minimum data gate while keeping candidate-visible pre-decision state, independent semantic oracle, hidden fixture truth, and post-decision/effect fields separate.

## T
Primary corpus is exactly 12 independent scenario units × 8 states = 96 rows. Each unit contains four positive decisions and four semantic negatives. The 8 row roles are fixed before generation: CLICK unique, CLICK multiple-acceptable, TYPE_TEXT payload-present, SCROLL multiple-acceptable, NO_LOCAL_ACTION, YIELD missing-target, YIELD ambiguous-target, and one rotating YIELD control from {stale-state, unsupported-operation, payload-missing}. Scenario units 0..7 are train and 8..11 eval; split occurs only by unit.

Candidate-visible packet may contain only intent identifier, current observation/state/binding identifiers, allowed operation vocabulary, caller payload-reference presence and current candidate descriptors. Hidden fixture truth, acceptable set, future/post-decision effect, teacher/chosen label and evaluator-only fields are separate and forbidden from candidate input.

Independent oracle is implemented separately from the generator's expected labels and returns a set of acceptable typed dispositions. Multiple acceptable actions remain multiple correct answers.

Construction uses two excluded scenario units with seed 113320260918000. Primary uses seed 113320260918001, exactly one invocation, reruns/replacements/tuning0.

## D
`READY_PURPOSEBUILT_OPERATION_TARGET_CORPUS_SCOPED` only if: rows=96; scenario units=12; positives>=32; semantic negatives>=32; executable operation families>=2; NO_LOCAL_ACTION>=8; YIELD>=8; target-alternative rows>=16; train/eval scenario sets are disjoint; candidate-visible packets contain no forbidden field; independent oracle exactly reproduces every acceptable-disposition set; corpus has no candidate-visible signature mapped to materially different acceptable sets; source/result/audit integrity passes; primary invocation1/reruns0.

Alias => `HOLD_CORPUS_ALIAS_OR_INSUFFICIENT_STATE`; count/split failure => `HOLD_CORPUS_BALANCE_OR_SPLIT_INSUFFICIENT`; leakage => `FAIL_ORACLE_LEAKAGE`; mismatch/integrity => `FAIL_INTEGRITY`.

## C
The fixture is deliberately controlled and hand-authored. Candidate extraction can do much of the work. READY establishes only that a leakage-free decision-level corpus can exist; it does not establish a learned residual, model competence or live safety.

## U / stop
No model training/inference, provider, GUI, OS task input, shared runtime or production ABI. Stop after one source-first corpus-generation block + independent audit. A later #1015 successor must first compare deterministic rules/macros on the frozen corpus before adding one shadow model.
