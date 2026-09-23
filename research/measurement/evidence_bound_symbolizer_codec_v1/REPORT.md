# Evidence-bound symbolizer codec — deterministic Rung0 result

Task `EVIDENCE-BOUND-SYMBOLIZER-CODEC-20260918-001`, parent Issue #1016.

## Disposition

Retain the formal science result as **`PASS_EVIDENCE_BOUND_SYMBOLIZER_CODEC_SCOPED` with an explicit frozen-auditor repair history**.

Formal invocation1/reruns0. The frozen runner's first outcome has all scientific gates at zero error, but the original frozen auditor returns `audit_pass=false` solely because its hard-coded fixture class-count expectation is 26/38 while the frozen 64-case fixture actually contains 27 `negative_or_uncertain` and 37 `supported` cases. The formal result itself records 27/37, exactly matching the immutable fixture.

No formal rerun, result edit, fixture edit or scientific source edit occurred. `AUDIT.json` remains false. A separately labelled postformal read-only `AUDIT_V2` derives category counts from the frozen fixture instead of hard-coding them and returns PASS/errors[].

## Frozen first outcome

- valid semantic cases: 64
- malformed/version/provenance/role faults: 32
- candidate/oracle mismatches: 0
- exact round-trip mismatches: 0
- deterministic render mismatches: 0
- candidate fault acceptances: 0
- oracle fault acceptances: 0
- evidence-role promotions: 0
- authority fields observed: 0
- coordinate/permission recovery: 0
- validity-dependency loss: 0
- model calls: 0
- task-input actions: 0

The valid corpus includes CLICK, TYPE_TEXT, bounded SCROLL, current target present/missing/ambiguous, historical stale target, predicted target and independently verified effect records. Role/source/state compatibility is fixed; intent/prediction/history cannot be decoded as current observation or verified effect.

## Representation diagnostic only

Canonical deterministic render bytes total: 10,609. Compact packet JSON bytes total: 8,459. Delta: -2,150 bytes in this frozen fixture. This is **not a token claim**, not model comprehension evidence and not an end-to-end context-saving result. Arbitrary symbol codes may tokenize poorly or require definitions that erase the byte difference.

## Audit repair / integrity

Original frozen `AUDIT.json`: FAIL `class_counts` only.

Diagnosis: frozen auditor expected 26/38, while direct frozen fixture count and RESULT both equal 27/37. No science source changed.

`AUDIT_V2.json`: PASS/errors[] using fixture-derived category counts. `CORRUPTION_V2.json`: 7/7 copied-result mutations rejected, including a wrong 26/38 class-count mutation. Postformal source rehash: 8/8 exact.

The preregistered corruption harness also reports rejection, but because its baseline frozen auditor is already false it is **non-discriminating and is not counted as integrity evidence**. V2 controls are the relevant read-only postformal integrity check.

## Scope / next discriminator

This closes only deterministic codec/rendering mechanics for #1016. It does not establish semantic extraction from natural language, local-model accuracy, token savings, task success or cross-application transfer.

#1014 remains the model-inference dependency. The next model-facing #1016 rung, if/when #1014 is mechanically ready, should hold this exact codec fixed and test only semantic mapping/abstention quality. Do not change model + symbol vocabulary + execution policy together.
