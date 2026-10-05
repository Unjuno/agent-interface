# Wheel cleanup on the #7974 successor

This connects existing wheel repair #7958 to #7974 at `a8053e32ef416717af5bc0e3a84fa267e5c18404`, replacing its former #7910 dependency. Original head `6a67276c1f336b58f3957b4cbe9d88a43ef44d3c` and its evidence remain in merge history. No force update, closure or deletion is needed. Parent: #59.

The two overlapping files were resolved to the exact #7974 V12 owner and cleanup test, then the existing two-line wheel hunk was reapplied: record button 4/5 after the per-notch pointer guard and before XTest emission. All 41 successor source/dependency files match except those two owner lines. The wheel regression is unchanged.

H: The successor still omits wheel inputs from cleanup tracking, permitting false verified cleanup after dropped UP or partial delivery. T: Replay the retained wheel cases against the exact successor, then the composition; check the combined owner suite and historical key/button cleanup mapping. D: Fail on a down wheel with verified cleanup, missing bounded cleanup attempt, redundant UP after success, or inherited owner regression. C: Old-base PASS does not prove this composition; XSync success is not release verification. U: Synthetic X server and actual local owner threads only; no live X, physical input, task effect or recovery claim.

## Retained results

- `red`: exact #7974 source, unchanged wheel test: 7 methods with 12 failing subcases.
- `green`: same 7 methods/18 subcases PASS after the two-line hunk. The source/test inventory changes only in `input_owner_v12.py`.
- `combined`: 14 V12 owner methods PASS, including the same 7 wheel methods. Covers key cancellation, dropped/retried keys, ordered batch, persistent loss, query failures and transport/button cleanup. Do not add 7 and 14 as independent coverage.
- `legacy-adapted`: one additional historical key/button cleanup test PASS. #7974 retries a dropped key UP before `up` returns, so the old intermediate assertion expecting `{65}` is changed to the stricter empty-state assertion. All final verification and no-duplicate key/button release counts remain unchanged. The original text is retained; it was inspected, not rerun unchanged against the new contract. Original #7910/#7958 results remain pinned to their old source.

Normal Python 3.12.14, macOS 27.0.1 arm64, existing dependencies; no installation or live/formal allocation. Private original logs and receipts remain intact. Published copies replace only repository, runtime and private-evidence absolute path prefixes; receipts retain original and published log hashes. Log durations are not latency measurements.

## Reproduce

From this proposal's repository root with the existing Python dependencies:

```sh
PYTHONPATH=research/live_control:research/doom python -B -m unittest discover -s research/live_control -p 'test_input_owner_v12*.py' -v
PYTHONPATH=research/live_control:research/doom python -B research/live_control/results/wheel-successor-regression-e0cc-20261005/legacy_cleanup_compatibility.py
```

For RED, use an isolated checkout with the candidate tests and replace only `input_owner_v12.py` by that file from the exact #7974 commit above. Each first invocation is retained with command, source hashes, timestamps, subprocess exit and logs. The 41-file successor manifest identifies the dependency closure; historical test source comes from the original #7958 head above. The scripts here are not test-discovery entry points and do not start a real backend.

## Review and integration boundary

The existing separate bugbot agent inspected the narrow composition, wheel test, receipt joins and legacy assertion change without rerunning tests. No material defect found. This technical review is not a quorum vote. Mid-batch cancellation/expiry has no direct regression here; no stronger timing claim is made.

This updates #7958, stacked on #7974. It does not merge main or resolve global XQueryKeymap/pointer ownership: ownership-sensitive use still requires an exclusive display or cooperative arbiter. Content votes and exact-tree nonauthor main integration remain outstanding.

Workflow files match the already inspected 249 YAML definitions at `0d08aa48521c343bdfb4936400910363a9d56eb6`; exact-ref formal jobs do not match this branch. The stacked base returned `Branch not protected`, and repository-plus-parent rulesets returned `[]` this turn. The publication merge commit uses `[skip ci]` only for supported push/pull-request events; no manual workflow or cancellation is requested. Main protection must be rechecked at actual integration.
