# R20 — complete supervised MCP suite on dedicated C: TEMP

## Frozen question and conditions

Does the complete 63-test `runtime.cli_v1.test_mcp_supervised_win32` module pass on the observer-binding candidate when temporary files use a dedicated C: worktree path? Conditions and source hashes were frozen in `conditions.json`. The suite ran once normally followed by once under `-O`, with no retries. This directly follows R16's failures on the default `D:\CodexData\Temp` path and R19's failed three-test D: comparison.

## Results

| Mode | Result | Duration | Exit |
|---|---:|---:|---:|
| Normal | 63/63 passed | 116.525 s | 0 |
| `-O` | 63/63 passed | 118.401 s | 0 |

Both logs report `OK`. The exact conditions, stdout/stderr logs and exit receipts are bound by `SHA256SUMS.txt`.

## Interpretation and limits

The full module passes under both interpreter modes on the dedicated C: temporary path. Combined with R16's D: failures and R19's D: errors/latency versus R18's same-group C: passes, temporary-storage location is a strong explanation for the broad R16 failure pattern. This is scoped test-environment evidence; it does not prove whether the underlying cause is storage latency, filesystem filtering, or file-lock behavior. Keep the R16 and R19 failures in the record.

This validates the observer-binding candidate's complete local test module under the recorded C: environment. It does not establish live GUI effects, standard-caller recovery reliability, MAP01, integrated efficiency, Research Preview acceptance, or overall project completion.
