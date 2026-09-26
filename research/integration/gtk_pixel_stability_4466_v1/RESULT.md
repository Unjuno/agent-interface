# Result — PASS_NO_INPUT_STABILITY_GATE_CALIBRATED (fixture scoped)

Allocation: `issue4466-visibility-formal01`

Frozen main: `c83ddb057c680a126144d000bf7ef7ba2274652a`

Docker image: `sha256:eb3ce9f5bd0cf358664b9d1ff9bce4cf2ce9f82f72ec700222046fb8fe8b96ba` (`linux/amd64`)

## Formal observation

The one frozen formal invocation completed all 15 captures in one private Xvfb session. There were zero model/provider/network calls, zero keyboard/pointer input, zero target effect/event files, and zero formal reruns. Target and decoy ran as distinct XID/PID pairs and retained the same title and 400×180 geometry. Every process was reaped; Xvfb exited 0.

- Unobscured target: three consecutive 400×180 captures were RGB-identical, all with 247 colors and RGB SHA-256 `d3a3d5ac7a5cc075444c65345ce07e32bb6def5b634701321af6ff02c724e016`.
- Same-size decoy stacked over target at `(0,0)`: all three target-window XWDs were RGB black (one color); each differed from baseline at all 72,000 pixels. The decoy image had 179 RGB colors.
- Decoy moved adjacent to target at `(400,0)`: all three target captures returned to the exact unobscured RGB hash. Both cross-stage comparisons changed all 72,000 pixels with full-frame bounding box `[0,0,399,179]`.

Both target and decoy reported `Map State: IsViewable` during overlap. The target XID/PID and geometry did not change. X11 focus remained `PointerRoot`, and `_NET_ACTIVE_WINDOW` was absent because the isolated Xvfb had no EWMH window manager. In this fixture, `IsViewable` alone does not mean the target's pixels are readable: an overlapping window made `xwd -id <target>` return a stable all-black image, and moving that window away restored the target RGB. Treat occluded/invalid captures as unavailable evidence, never as an application effect.

## Independent audit and retained anomaly

The frozen v1 auditor independently recomputed the evidence but failed while serializing its result because its identity map used tuple keys. The original error is retained in `evidence/audit-v1-execution-error.json`; the frozen auditor source and formal raw evidence remain unchanged.

Posthoc auditor v2 was run once in a separate network-disabled, read-only-source container against the same read-only `formal01` bytes. A source diff confirms its only logic-adjacent changes are converting identity keys to JSON strings and labelling its scope as posthoc; capture expectations, thresholds, source-hash checks, and outcome gates are unchanged. V2 independently returned `PASS_NO_INPUT_STABILITY_GATE_CALIBRATED`, 15/15 rows, zero errors, and all frozen source/raw hashes matching. The first audit error remains visible and is not replaced by the v2 artifact.

The standalone auditor self-test passed before freeze: missing and reordered capture rows were rejected, a one-RGB-pixel change was detected, and changes limited to the unused XWD high byte were ignored. Construction failures and intermediate runs are retained separately under `evidence/construction01/` through `construction05/`; none count as formal observations.

## Scope

This calibrates XWD visibility behavior for this GTK3/Xvfb fixture and this exact capture path. It does not establish application-effect detection, task success, general window-manager behavior, adapter `partial/task_success=null` reconciliation, full #3240 completion, or #2606 acceptance. The complete raw bundle and audit manifests are under `evidence/`; see `PREREG.md` and `FREEZE.json` before reuse.
