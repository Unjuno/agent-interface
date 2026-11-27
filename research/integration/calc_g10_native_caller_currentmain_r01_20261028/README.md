# Calc G10 current-main Fake X recheck (2026-10-28)

This is a bounded offline rerun of the committed G10-shaped adapter/current caller composition. The original test source was materialized from the current checkout's skip-worktree entry and byte-checked against `HEAD`; the source commit before the fixture correction was `0897421623612f13d83c1994ab06dd21408a2855`.

## Preserved first outcome

On Windows CPython 3.11.9, the original positive test stopped safely after one completed and released synthetic transition with `SAFE_YIELD / missing_symbol`. No second alias or second click occurred, and the outer scorer was skipped. The retained diagnostic reports zero elapsed time and equal-valued event timestamps. The adapter's private action-return boundary was not serialized, so the suspected same-tick capture condition is consistent with the evidence but is not directly proven by the first receipt. The failed test output and returned state are retained as `attempt-01-*`.

## Fixture correction and result

The positive fixture now injects an incrementing monotonic nanosecond clock only around the composed run and records/asserts that the second capture timestamp is strictly later than the first action-return boundary. This makes the intended fresh-capture ordering deterministic on coarse-tick hosts. Production freshness checks and runtime code are unchanged. The first failed outcome remains preserved.

- Focused module: 2/2 tests passed under normal Python and `-O` before the explicit timestamp assertion was added; those logs are retained as `pass-before-clock-order-assertion-*`.
- Selected integration closure: 25/25 tests passed under normal and optimized Python (`-O`) with the final assertion across the native caller, fresh admission, caller scoring/entry, bounded proposal, current core, stale guard, retained OCR inputs and tri-state composition. Full logs and exit codes are saved.
- Environment: Windows CPython 3.11.9, actual `NativeHandleBridge`/compiled core/caller with Fake X transport and synthetic application effects. No live Calc, X server, OCR process, model call, Docker container, WSLc allocation or independent task oracle was used.

The positive test's `TASK_SUCCEEDED` result is confined to the synthetic outer effect callback. This packet validates a local composition contract and monotonic fixture ordering only; it does not validate live Calc recognition, native release, model costs or the matched cold/warm/invalidation/repair comparison.

The updated regression is `research/integration/test_calc_g10_native_caller_composition_v1.py`. `SHA256SUMS` covers all packet files, the regression source, and the crosswalk.

## Fresh focused rerun (2026-10-28)

The focused two-test composition module was rerun after the prior packet was recorded. `runtime.cli_v1.test_calc_g10_native_caller_composition_v1` passed 2/2 in normal Python and 2/2 under `-O`; both process exit codes were 0. `TEMP` and `TMP` were directed to `D:\CodexData\Temp\agent-interface-test-tmp-r01` because C: was full. Logs and exit codes are `fresh-focused-*`; commands are retained in `FRESH_COMMANDS.txt`. This reconfirms only the offline Fake X composition and deterministic fixture clock, not the 25-test closure, live Calc, or the efficiency comparison.
