# R05 callback Future drain diagnostic

## Frozen question
Does tracking each run_coroutine_threadsafe API future and draining outstanding futures before interface_close and TemporaryDirectory teardown eliminate the observed in-flight .report.json.tmp cleanup collision, while preserving the original 8s callback timeout and exact-once/no-replay safety conditions?

## Pre-registered conditions
See conditions.json: six fresh processes (three normal, three optimized), interleaved in one fixed order; no retries or replacements. This diagnostic modifies the existing test harness only. It preserves the 8-second callback timeout, exact operation and generation requirements, one action, no replay, and the frozen product code from main 19d4752e.

## Recorded outcome dimensions
For every trial, preserve the exact unit test result, per-operation callback exceptions, whether each future was complete at teardown, whether outstanding futures drained within 30 seconds, and whether teardown encountered an in-flight .report.json.tmp deletion error. Any behavior failure remains a failed attempt even if cleanup completes.

## Interpretation boundary
This test-harness experiment can establish whether test teardown races an outstanding API coroutine. It cannot explain R04's runtime timing variance beyond those captured callback details and cannot establish production recovery reliability, native task effect, MAP01, efficiency, WSLc, preview acceptance, or runtime distribution.
