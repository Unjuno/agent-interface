# Predictive safety filter T3

This additive Issue #5317 allocation exhaustively checks held-out combinations of finite-state intent predicates. It does not alter T0/T1/T2.

The exact source hashes, base commit, and enumerated workload are pinned in FREEZE.json.
The study and independent audit are pure JavaScript function expressions using standard ECMAScript features. They were invoked separately in the Codex functions.exec V8 isolate; both are also usable from a Node.js harness that evaluates the file contents and calls the returned function.

The source runner enumerates every four-action sequence in the frozen alphabet under four held-out constraint compositions. The auditor independently enumerates with numeric action IDs and a separate predicate evaluator, then verifies the complete result and output mutation controls.

No container slot was assigned, and no external input/output occurs in this finite-state test. The result is not evidence of runtime safety, GUI correctness, or task benefit.
