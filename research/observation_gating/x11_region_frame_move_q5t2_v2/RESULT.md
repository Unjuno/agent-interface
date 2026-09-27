# Formal result — Issue #4902 / successor to #4439

**Disposition: `PASS_X11_REGION_FRAME_MOVE_BOUNDARY_SCOPED`.** One frozen local Docker runner invocation completed 27/27 fresh Xvfb sessions. The raw-only auditor reported `errors=[]`; all 14/14 corruption controls rejected their mutation. No GPU was used because X11 geometry/capture is CPU-bound.

| Policy | STABLE | MOVE_BEFORE | MOVE_BETWEEN |
|---|---:|---:|---:|
| PINNED_SCREEN | 3/3 match | 0/3 match | 0/3 match |
| REFRESH_SCREEN | 3/3 match | 3/3 match | 0/3 match |
| WINDOW_CLIENT | 3/3 match | 3/3 match | 3/3 match |

This supports only the frozen X11 coordinate-frame result: a pinned screen rectangle becomes stale after movement; refreshed root geometry works if resolved after the move but remains vulnerable to the directed resolve→move→capture interval; direct capture from the same live window XID remained equal to the scoring oracle in all tested schedules. A mismatch is stale-coordinate observation, not target absence or action authority.

## Provenance

- Runner SHA-256: `6c7d86c6ffc3c3bbcce45086fe52572d36267b5cc5b0647711a3db43c3f2d17c`
- Auditor SHA-256: `a3cdb1ea959deccca87b9a7f2387f754cedd624426caf358cdf5726b13743c97`
- Docker image ID: `sha256:1c334ebd65f4b1bfe81cc84c90780ea01e6f70c0f7b18cd89c09e03406460238` (`linux/amd64`, offline, `--pull=never`, `--network none`)
- Formal invocation: 1; rows: 27; replacements/retries/exclusions: 0
- Raw JSONL: 70,872 bytes, SHA-256 `1bd3ae25aacc2dd182762c7389b685831ee731e61c598c9c285a0009607ee530`
- Audit JSON: 1,533 bytes, SHA-256 `1920127ce948b835ce80830ccfc9a132fb632f9fcf4e064b8cf72f72e4fabb66`
- Audit gates: `errors=[]`; 14/14 copied corruptions rejected; `passed=true`

The raw records retain candidate/oracle/exposed pixel payloads and hashes, geometry, monotonic capture brackets, Xvfb exit/log receipts, and Xauthority mode. The run used the frozen direct-Xlib fixture because the cached image has no Tk libraries; this is not a Tk result. A predecessor allocation stopped before case 0 due only to an output-mount collision and remains unchanged; see [its STOP receipt](https://github.com/Unjuno/agent-interface/blob/research/x11-region-frame-move-4439-20260927/research/observation_gating/x11_region_frame_move_q5t2_v1/FORMAL_01_STOP.json).

## Limits

One synthetic window/image, host and Xvfb implementation. No claim about Tk, Wayland/compositors, async races, semantic target identity, occlusion, lifecycle, freshness at model consumption, input/replay/task-success authority, latency, model utility, or production readiness. Construction-only and synthetic auditor-shape rows are not included in this formal denominator.
