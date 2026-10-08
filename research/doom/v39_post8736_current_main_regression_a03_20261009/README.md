# V39 focused regression replay on exact current main

## H/T/D/C/U

**H.** The exact current-main source closure for the V39 controller, V15 session, Executor V13 and explicit-UP cancellation remains clean under the focused source/fake-X regression.

**T.** Freeze at `ffe5292b3164a3eb7e2b5d18eaadcbafdcd2b385`; run the same seven modules previously tested by PR #8731 in normal and optimized CPython 3.12.14. Independently reconcile all 73 static-closure Git blob IDs against that exact commit and verify saved logs/results.

**D.** Both modes pass all 107 tests, all 73 closure blobs match the frozen current-main commit, and the saved-only verifier reports `PASS_SAVED_EVIDENCE`.

**C.** This is a focused regression suite, not the full project suite or a live episode. The closure is the same AST-derived closure defined in PR #8731.

**U.** This confirms only current-main source/fake-X regressions. It does not test physical input, game/model/GUI behavior, live threat response, useful task effect, recovery efficacy, safety, or MAP01 completion. No live allocation was used or authorized. PR #8731's earlier b404 snapshot evidence remains unchanged.

## Commands and custody

See `COMMANDS.txt`, `FREEZE.json`, `RESULT.json`, `results/`, and `SHA256SUMS.txt`. `audit.py` checks the frozen identity, all 73 closure entries, exact 107-test receipts, and scope declaration; it does not rerun the tests.

## Saved-evidence audit integrity follow-up

The initial saved-only verifier did not join the allocation, source-closure, scope, and exit-receipt records. Its v2 now checks those cross-record bindings plus all seven frozen module names and runtime identity. Six ordinary corruption controls reject a foreign commit, allocation ID, closure count, scope promotion, exit mismatch, or test-log count mismatch. The package remains a source/fake-X replay only; these controls add no execution or live evidence.

Construction commands:

```text
python3 -B -m unittest -v research.doom.v39_post8736_current_main_regression_a03_20261009.test_audit
python3 -O -B -m unittest -v research.doom.v39_post8736_current_main_regression_a03_20261009.test_audit
python3 research/doom/v39_post8736_current_main_regression_a03_20261009/audit.py
```

Both test modes pass 6/6. The auditor reports `PASS_SAVED_EVIDENCE` and explicitly does not claim a formal or independent rerun.
