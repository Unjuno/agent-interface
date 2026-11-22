# R22 — final scoped observer correction, combined MCP modules

## Result

After CI revealed that binding also changed one-shot observer monkeypatch behavior, the ordinary/non-supervised branch was restored to module-global `observe`; only `supervised-win32` uses the per-server bound observer. With short dedicated C: TEMP roots, the complete ordinary MCP and supervised MCP modules passed together:

| Mode | Tests | Duration | Exit |
|---|---:|---:|---:|
| Normal | 94/94 | 121.368 s | 0 |
| `-O` | 94/94 | 122.586 s | 0 |

Both logs report `OK`. Conditions and source hashes are frozen in `conditions.json`; raw output and exit receipts are included in the packet manifest.

## Scope

This validates the final candidate against the two directly affected MCP modules and confirms the supervised observer binding while preserving the ordinary observer lookup behavior. It does not prove the historical R10 cause or live Win32 task effect, recovery reliability, MAP01, efficiency, Research Preview, distribution, or project completion.

## Related failed/diagnostic runs

- R16/R19 preserve D: temp-volume delays and cleanup errors.
- R20 passed the supervised module before the one-shot branch scope correction.
- R21's 94-test attempt used a deep TEMP path and failed only the portable stdio child launch with WinError 267.
- R22 uses a short C: TEMP path and passes the 94-test combined scope in both modes.

Keep every earlier outcome; R22 supersedes them only as validation of the final scoped source.
