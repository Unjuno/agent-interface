# Issue #57 composition R01: adaptive caller v3 with compiled GUI runtime

## Result

On exact current main c4065d011e1297ebd589bcd5b85da3beb269e037, a new two-case composition test connects the shared adaptive acquisition caller v3 to runtime.core_v1.compiled_gui through the caller execute adapter.

The positive path runs the complete cold caller route with two accounted synthetic model attempts (coarse candidate and grounded target reference). The compiled runtime then performs two fresh observe/admit/execute/release transitions; the intermediate observation selects the second operation locally, with zero internal frontier-model resumptions. Task effect is checked by a separate outer scorer after program completion. Exact usage totals, task success, effect receipt, and local runtime receipt are asserted.

The changed-intermediate-evidence path retains the first verified action and release, then refuses a second admission/input when the submit predicate disappears. The outer caller returns EXECUTION_INCOMPLETE / unknown_state / confirmed_partial; the independent task scorer is not called and task success stays unset.

Focused composition tests pass 2/2. The caller v3 suite plus 17 compiled-runtime custody/ordering/release modules pass 132/132 in normal and 132/132 under -O on Windows CPython 3.13.14.

One focused implementation smoke ran before condition freeze; its console output was not retained and it is excluded from the result. The first broad normal bundle invocation had one setup import failure because the legacy caller test imports adaptive_acquisition_caller_v3 as a top-level module. Its complete raw outputs are preserved under preliminary_setup_failure_* and excluded. The corrected runner sets PYTHONPATH to both repository root and research/live_control; all corrected normal and optimized runs passed.

## Scope and limits

Every model, observation, admission, action, release, and task-score callback is synthetic. No external provider, live GUI/application, allocation, or real custody attestation was used. This is composition correctness evidence, not a measured efficiency comparison, reliability estimate, or Research Preview acceptance.

## Custody

CONDITIONS.json pins current main, source/test and runner hashes, module list, pass rules, and the harness correction. Per-module command, stdout/stderr byte streams, and exit codes are retained in this directory. SHA256SUMS covers every retained file.
