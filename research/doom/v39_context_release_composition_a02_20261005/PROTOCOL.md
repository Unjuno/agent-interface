# V39 context and per-key release composition A02

## H — hypothesis

A synthetic merge of current main with PR #7783 (the exact owner admission-ID projection fix atop #7602), PR #7750 (owner-issued per-admission identity and release receipts), and PR #7769 (per-key cancellation cleanup) has no source conflicts and passes the three component-focused suites together.

## T — test

The frozen heads and order are in `FREEZE.json`. Build the three Git merge-tree steps in that order, materialize only the source paths required by the suites, and run each command once with the frozen CPython runtime. Preserve command output and return codes. Record source blob IDs from the final composition tree. A separate read-only auditor checks merge parents/tree IDs, all frozen heads, source blobs, and output counts.

## D — decision

`PASS_COMPOSITION_SCOPED` requires three clean merges, exact reproduction of the final tree, and 37 + 3 + 3 passing tests with exit code zero. A merge conflict or test failure is retained as `FAIL_COMPOSITION`; missing source or a defective test environment is `HOLD_CONSTRUCTION`. Do not repair or rerun within this attempt.

## C — competing explanations

A clean merge and passing focused tests can still miss runtime ordering, real X11 owner timing, application input consumption, or useful feedback/recovery behavior. The existing `native-mcp` failures on #7750 are a distinct failing suite and are not erased by these focused composition tests.

## U — limits

This is synthetic source composition only. It neither approves nor merges the open component PRs and does not authorize a live #59 allocation. It establishes no real-input, gameplay, task-effect, safety, latency, survival, recovery, or MAP01 claim.
