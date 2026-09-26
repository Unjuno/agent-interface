# Issue #4536 offline regression result

Status: **HOLD — final-admission production function regression passes; monitor/adapter integration and formal MAP01 gate remain unverified.**

## Scope and hypothesis

This additive deterministic regression tests the Issue #4536 clock-domain hypothesis only. It consumes the retained #4516 seed-990637 clock calibration as read-only fixture data and imports the exact `final_action_admission_v1.py` production function. It does not rerun that allocation, start the game or planner, or call an input backend. The historical missing invalidation receipt means this cannot establish that a hard policy invalidation caused the predecessor exception. Sparse checkout omitted the `research/live_control` subtree, so the production function was materialized read-only from `HEAD` into `/tmp/issue4536-live-control` for the local test; container validation must mount the exact tracked source file.

The modeled contract requires host-domain invalidation time to be translated with a validated same-session offset interval before comparison with the runtime-domain controller decision. It preserves both original and converted timestamps, rejects an interrupted/stale decision, and grants no executor input authority.

## Local validation

Command: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s research/doom/map01_policy_invalidation_clock_4536_v1 -v`

Result: **PASS, 7/7**. The exact production final-admission function reproduces `controller decision precedes observed boundary` with the mixed-domain value and returns `REJECTED_POLICY_INVALIDATED` with no input authority after calibrated conversion. The deterministic contract also verifies zero modeled input calls and retention of both clock-domain values; stale-session, over-wide calibration, and invalidation-after-decision controls fail closed.

## Pinned-container validation

Image: `issue2679-map01-runtime:20260921-pinned`, digest `sha256:029e1867aeb843f2d63080343bfbb61540b64852ce00d4d99ec0be51796a093e`.

Run used `--network none --read-only`, read-only mounts for the model, predecessor calibration fixture, and exact tracked final-admission source, and `--entrypoint python` to bypass the image's MAP01 runner entrypoint. Result: **PASS, 7/7**. No model, GPU, game, or input call occurred.

## Gate boundary / next step

This validates the final-admission function against typed synthetic receipts, but not the real monitor/adapter integration or a captured live invalidation receipt; therefore it does not prove that the real stale turn is stopped before Executor input and no formal allocation is authorized by this result. Next locally test the actual production monitor/adapter boundary with a captured typed receipt and retained calibration; only if that gate passes should the one fresh seed/path preflight and formal allocation be considered under #4536.
