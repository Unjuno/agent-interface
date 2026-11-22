# R10 dispatch report-finalization and teardown drain

## Evidence-based question
R09 retained three failures in a fresh 10-run cohort. One optimized attempt surfaced an exact terminal action before the corresponding `report.json` was finalized; its fixed 2-second wait expired and TemporaryDirectory teardown collided with an in-flight `.report.json.tmp`. The caller API Future drain did not cover the separately spawned dispatch worker. R10 tests that exact remaining seam.

## Frozen intervention
Keep runtime/server code, action semantics, 8-second callback call timeout, 10-second exact result-poll window, and pass criteria unchanged. In the harness, continue polling rather than failing at the nested 2-second file check, but only until the already-frozen 10-second result deadline. Before fixture teardown, wait up to 30 seconds for each exact dispatch report to be finalized (read-only report/path checks only), then request `interface_close`; retry close only if it returns busy. No observe/dispatch/task-oracle retry or replacement. Use five fresh normal and five fresh `-O` processes in the fixed interleaved order.

## Safety and interpretation
A finite report/worker drain cannot upgrade task success or release; the existing exact independent-oracle and no-replay checks remain. This is test-harness Fake/local evidence and cannot prove native GUI or production reliability.
