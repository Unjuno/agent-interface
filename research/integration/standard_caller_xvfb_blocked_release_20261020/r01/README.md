# Standard MCP blocked-owner release on private Xvfb — r01 (2026-10-20)

## Question and condition

Does the standard MCP caller retire an owner blocked in real Xlib I/O, confirm that exact X client disconnected, and use an independent X connection to release an already-held key within a finite bound while a delayed request is still pending?

The test used a private workflow-owned Xvfb on Ubuntu. It delivered `KeyPress(a)` to a synthetic application, queued an 8,000 ms delayed `KeyPress(b)` on the same owner connection, then blocked the owner in python-xlib `Display.sync()`. The X server remained responsive to independent connections. The normal caller cancelled and retired the owner; a PID-qualified XRes observer confirmed disconnect; a separate bounded worker sent release and read back the keymap; an independent synthetic task oracle checked the application property and both keys through the delayed-request horizon.

## Frozen source and runner

- PR #9225 exact head: `ce72668b596df1b67dd58db4cf26d25a10d85a5b`; merged main: `a8013b1bd24e9d55f45318e3b8f7d4dbfb31a1f9`.
- Workflow run [39376306302](https://github.com/Unjuno/agent-interface/actions/runs/39376306302), job `x11-integration`, passed. The run was on PR #9225; the report records workflow merge SHA `d41347e7ad538c8a55b5b7206f00997cf70a485a`.
- Test source blob `runtime/cli_v1/test_mcp_xvfb_blocked_release_integration.py`: `62364f6f0678549985b286f0946e639be99299bd`; workflow blob `.github/workflows/runtime-x11-v1.yml`: `7a55cdd03b0a21f595860d8ba9166b4863008106`.
- Runner: Linux x86_64, Python 3.12.15, Xvfb package `2:21.1.12-1ubuntu1.9`, binary SHA-256 `0081b27338b510ec5e2068a93c6db31480872de9bb082f347f3747ef1648e794`.
- Artifact files were downloaded without editing. `SHA256SUMS` records each retained JSON report and observation image.

## Observed outcome

Five trials in that single workflow job passed the test's synthetic independent task oracle. Initial and final application property values were `[1]`; both `a` and `b` were up at independent release readback and at the delayed-request horizon; no delayed `b` press was observed. The test checked 64-hex process and window generations before dispatch. Reproduce the raw-only checks with `python research/integration/standard_caller_xvfb_blocked_release_20261020/audit_raw.py`; derived values are saved in `audit-summary.json`.

Across the five reports:

| Measure | Observed range |
|---|---:|
| `interface_guarded_cancel` return | 675.176–935.623 ms (declared caller bound: 3,000 ms) |
| PID-qualified owner-client disconnect | 73.194–77.386 ms |
| Independent release attempt through verified keymap readback | 595.514–622.932 ms |

One trial used a 1 s injected cancel-ack delay. Four trace-comparison trials used zero delay, with owner-process method tracing disabled twice and enabled twice. These are repeated measurements within one runner and one Xvfb server lifetime, not five independent environment replications.

## Required qualification and limits

This is a scoped positive observation for the exact standard caller, Xvfb package, delayed-request schedule, synthetic application, and task oracle. It shows a bounded release worker can act while the owner is blocked in `Display.sync()` if the server remains responsive to the release connection.

The caller still reported `cancel_unconfirmed`, `release_confirmed=false`, `cleanup_status=UNKNOWN`, `task_success=null`, and `replay_allowed=false`; the separate oracle's `task_success=true` does not override that conservative runtime receipt. The terminal result also contains an owner-process snapshot marked alive after the cancellation receipt says the same PID was retired. The terminal snapshot has no capture timestamp, so it may be an earlier concurrent snapshot; preserve this contradiction and reconcile receipt timing before promoting caller-level confirmation.

This did not stop the X server. The separate server-stop test remains a failure case: while the whole X server is stopped, disconnect and release cannot be confirmed until service returns. This packet does not establish physical desktop input, another X server/backend, MAP01, general recovery, a population reliability rate, or integrated efficiency. Keep Issue #17 open.

## Next discriminator

The current working copy now adds `liveness_observed_monotonic_ns` to owner-process snapshots and the Xvfb integration test checks its ordering against cancel return; the focused local suite passes. A fresh Linux Xvfb run is still needed to validate that correction in the live caller. Then run a separately versioned schedule with varied delayed-request timing and an independently rechecked target generation after recovery. Keep full-server stop as its own arm and retain UNKNOWN when its bound is exceeded. No WSLc allocation was used or renewed.
