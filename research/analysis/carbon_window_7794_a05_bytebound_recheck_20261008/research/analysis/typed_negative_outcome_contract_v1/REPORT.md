# Typed negative outcome contract v1 — Result

Issue #4174. Allocation `typed-negative-outcome-4174-20260923-01`.

## Result

**PASS_TYPED_NEGATIVE_OUTCOME_CONTRACT_SCOPED**. One formal invocation, 80/80 frozen rows, no reruns/replacements/tuning. Frozen independent audit: 415 checks, errors=[]; comparator counterexamples: futile retry 22, premature terminal 40. Authority is false on every row.

The preregistered corruption gate requires >=10 coherent evidence mutations to reject. The frozen controls rejected 11/12. The sole non-rejection, `retry_context`, was a harness no-op: it set row16 from `IDENTICAL_RETRY_VALID` to the same value. This made the frozen controls command exit1 after the scientific audit had already passed; it is retained as a tooling defect, not silently repaired. The remaining 11 real mutations satisfy the >=10 gate.

A separately labelled postformal control changes current+complete BLOCKED row18 from `REQUIRES_CHANGE` to `IDENTICAL_RETRY_VALID`; the unchanged frozen audit rejects that effective mutation. A postformal schema audit also accepts the untouched formal bytes. No formal corpus was rerun and the first audit/result are unchanged.

## H/T/D/C/U

- H: explicit evidence can preserve uncertainty/retry guidance where coarse status+timeout loses distinctions.
- T: authored deterministic standard-library 80-row corpus; provided Linux x86_64 container / CPython 3.13.5; no Docker image identity, GUI, model, provider, task input or network experiment.
- D: all frozen candidate rows match the independent oracle; stale/incomplete/contradictory evidence becomes FAILED_UNKNOWN; comparator exposes both required counterexample classes; 11 real frozen evidence mutations reject (gate >=10).
- C: specification fixture with authored truth; coarse comparator is intentionally incomplete and is not alleged to be production behavior.
- U: real planner comprehension, live Calc/OpenTTD evidence, token/schema cost, recovery quality, natural failure frequencies and production integration remain unknown.

## Integrity

Formal raw SHA-256: `b0a0ad24031ab50e0f410c78de6b4525edeae91ada87c787154bb8232024f117`. Lossless compressed Base64 plus `unpack_formal.py` reproduces the exact raw JSON. `FREEZE.json` binds the preformal source/corpus/environment hashes. Construction 5/5 passed before formal.

## Integration meaning

This scoped PASS supports carrying typed uncertainty/retry/required-change semantics into a later matched planner-facing trial. It does not show a model will use the vocabulary correctly or that extra schema cost is beneficial. Parent #39 remains open.
