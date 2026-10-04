# V39 sample-layer application-consumption conflict — A01

## H

If a per-key measurement says application consumption was not observed, an explicit contradictory or malformed `application_consumption_observed` value in a timing sample must invalidate the bracket and withhold both intervals.

## T

Frozen baseline is the refreshed PR #7662 head `a1cbc360d59ca90ceb6cc5cf2ca31be5e64c0414`. Replay the retained positive DOWN/UP pair against the baseline and candidate projector. Mutate each of six evidence layers on both rows with five non-`false` values: boolean true, integer one, integer zero, null, and string `false`. The untouched positive must remain paired.

## D

- RED on the parent: the regression failed on the four `true` mutations in `pre_sample` and `post_sample` across DOWN/UP rows.
- Full matrix: 60 mutations; parent accepts 20 contradictory timing-sample claims; candidate accepts 0.
- Candidate returns `adapter_edge_receipt_incomplete` and null intervals for all 60 mutations; positive control remains paired.
- Targeted regression 1/1 PASS; Python compilation and diff check pass.
- The full typed-feedback module ran 30 tests: 28 passed, while two fixture-dependent tests errored because the sparse worktree omits retained trace files.
- Independent saved-result/hash audit: `PASS_SAVED_RESULT_AUDIT`.

## C / U

This is AST-extracted deterministic projection evidence using retained construction rows. It does not test an X server, physical dwell, game, model, application consumption, useful task feedback, recovery, or live allocation. The live #59 threat-control gate remains open.

Raw JSON, baseline/candidate source snapshots, input rows, test snapshot, command outputs, and hashes are retained in this directory.
