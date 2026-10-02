# Construction history

1. TDD RED: both contract tests failed because the not-yet-created candidate program did not exist (exit 2); no candidate experiment was run.
2. Added a nine-case fixture, bounded candidate, and a separate auditor with an independently written oracle. Construction tests then exposed one wrong expected baseline-repeat count (the frozen fixture has one such row); corrected the assertion before formal execution.
3. Final construction suite: 2/2 passed; candidate and auditor compile. The five auditor mutations alter the frozen request label, scope binding, post-count, effect-authorized flag, or safety-release decision; each is checked against the independent oracle.
4. Formal candidate and auditor invocations remain pending until a final byte freeze and execution record are saved. No formal candidate/auditor call has yet occurred.

