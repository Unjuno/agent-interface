# Public MCP recovered-caller task-oracle composition R01

**Disposition: `PASS_FAKE_LOCAL_PUBLIC_MCP_COMPOSITION_ONLY`.** Frozen source is current main `b0bc13d71fd204e39d040584c2e3e9207a7879dd`, plus this branch's two source changes. The focused positive recovery composition and fail-closed unknown-custody control passed 2/2 normally and 2/2 under `-O` on CPython 3.11.9 / Windows 11 Pro build 26300.

## What the experiment establishes

The public `create_server` MCP path joined `interface_observe`, `interface_dispatch`, exact-call `interface_results`, and `interface_verify_task` for a compiled caller. In the recovery arm, the fake producer recorded the exact operation and target-generation task effect and then lost its completion receipt. The caller obtained an automatic recovery receipt with confirmed release and a validated synthetic late-input horizon. The caller returned `SAFE_YIELD / delivery_uncertain`, completed zero graph transitions, and retained the source action as `unknown` with `task_success: null`, source `release_confirmed: false`, and replay denied. The distinct task oracle accepted the matching operation/generation effect and reported task success. The task verdict did not change action, cancellation, or graph-completion state.

This exposed an integration gap: `interface_verify_task` previously accepted only completed/recovered action status, so it refused to call the independent oracle for an automatically recovered completion whose action correctly remained UNKNOWN, even when separate recovery custody proved release and the late-input horizon. Eligibility now also accepts this exact combination: action UNKNOWN, cancellation recovered, automatic completion recovery true, release confirmed true, and `late_input_horizon_verified` true. Missing/invalid horizon and other unknown custody remain ineligible; the existing fail-closed test for unknown public custody passes in both modes.

## Limits

All MCP server, producer, task effect, horizon, and oracle evidence here are fixtures. This single recovery arm uses a 10-second graph budget, 30-second fixture authority, and 8-second MCP callback waits. Those are finite test bounds, not latency measurements. Earlier normal retries failed at the observation deadline, method budget, or report-temp finalization under this host's scheduling; their exact outputs are retained in `raw/normal-*-failure.*`. The final one-attempt scenario passed without changing its oracle, release, horizon, or UNKNOWN-state acceptance conditions. This is not live Win32/MAP01 input, a real application task effect, repeated reliability, a matched efficiency comparison, WSLc/Docker evidence, Research Preview acceptance, or distributable-runtime acceptance. The evidence does not establish a production release decision. Issue #57 and the project-wide goal remain open.

## Frozen inputs and raw output

`conditions.json` pins the source/test hashes, exact commands, environment, finite scenario, and boundaries. The successful normal and optimized positive logs are `raw/normal.log` and `raw/optimized.log`; fail-closed controls are in `raw/normal-negative.log` and `raw/optimized-negative.log`. Adjacent `.exit` files record zero exit status. Several earlier failures are preserved with their exact console output in `raw/normal-*-failure.*` and `raw/normal-invalid-fixture-budget.*`. The early optimized pre-fix failure was not captured to a file. `SHA256SUMS.txt` covers packet files other than itself.

## Next gate

Keep #57 open. Freeze fresh attempts across independent fixture lifecycles with the negative controls (no horizon, mismatched operation/generation, and missing key-up receipt) and collect complete per-attempt receipts. Then progress to native task-effect/recovery evidence and repeated reliability. Do not infer real-world reliability or speed from this fixture pass.
