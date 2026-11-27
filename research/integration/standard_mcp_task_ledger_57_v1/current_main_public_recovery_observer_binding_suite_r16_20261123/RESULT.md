# R16 — full supervised MCP regression suite

## Question and frozen conditions

Does the complete `runtime.cli_v1.test_mcp_supervised_win32` module pass after per-server observer binding and public-caller receipt instrumentation? The two invocations were frozen in `conditions.json` against main `19d4752ed16063d63119f5d7347c51fb69f44a8c`, Windows CPython 3.11.9, one normal invocation followed by one optimized (`-O`) invocation, with no retries. Source hashes are included in the conditions file.

## Results

| Mode | Result | Duration |
|---|---:|---:|
| Normal | 63 tests; 12 errors; exit 1 | 527.637 s |
| `-O` | 63 tests; 12 failures and 16 errors; exit 1 | 867.312 s |

Neither invocation passed. The long serial run produced widespread failures in timing-sensitive caller/recovery tests and errors involving temporary request/report files and cleanup. The run-level interference and exact per-test failure/traceback lines are retained in `raw/summary-lines.txt` and the full logs. This suite result cannot distinguish a code regression from test-runner/worker/temp-file contention for every affected case; it must not be described as a passing candidate regression gate or a measured reliability cohort.

## Interpretation

The focused R14 server-bound-observer test and R15 public-caller callback-receipt test each passed their individually frozen normal and `-O` runs (1/1 per mode). R16 does not invalidate those focused observations, but it shows the monolithic 63-test module is not a usable acceptance measurement under this host/run configuration. It also does not prove that the historical R10 orphan came from late module-global observer lookup.

The next check should use fresh isolated processes for the narrow dependencies touched by this candidate and preserve worker/callback/temp-path receipts. Do not repeat the whole module unchanged; diagnose the source of temporary-file contention and timing spillover first. No live GUI, provider/model call, external input, task effect, reliability estimate, or efficiency result was produced.

### Follow-up qualification (R17–R20)

The three selected failures passed in isolated processes (R17) and together in one process per mode with dedicated C: TEMP (R18). The same group failed slowly under `D:\CodexData\Temp` with report-temp cleanup errors and a timeout (R19). The full 63-test module then passed in both modes on dedicated C: TEMP (R20). This makes the D: temp path/storage behavior the leading explanation for R16's host-run failures, without determining the precise filesystem/filter cause. R16 remains an observed failed run and is not overwritten by the follow-up.

## Raw custody

See `SHA256SUMS.txt` for the exact frozen conditions, both logs, exit receipts, and extracted outcome lines. The raw logs are authoritative; the summary file is a navigation aid.
