# Issue #4536 offline regression result

Status: **HOLD — model-level contract passes; production boundary and formal MAP01 gate remain unverified.**

## Scope and hypothesis

This additive deterministic model tests the Issue #4536 clock-domain hypothesis only. It consumes the retained #4516 seed-990637 clock calibration as read-only fixture data. It does not rerun that allocation, start the game or planner, or call an input backend. The historical missing invalidation receipt means this cannot establish that a hard policy invalidation caused the predecessor exception. Repository intake located `ObservableSignalPolicyMonitor` in `research/live_control/observable_signal_guard_v2.py` and the final gate in `final_action_admission_v2.py`; this model does not exercise either production module.

The modeled contract requires host-domain invalidation time to be translated with a validated same-session offset interval before comparison with the runtime-domain controller decision. It preserves both original and converted timestamps, rejects an interrupted/stale decision, and grants no executor input authority.

## Local validation

Command: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s research/doom/map01_policy_invalidation_clock_4536_v1 -v`

Result: **PASS, 5/5**. The mixed-domain unadapted case raises; calibrated conversion returns `REJECTED_POLICY_INVALIDATED` with zero input calls and both clock-domain values retained; stale-session, over-wide calibration, and invalidation-after-decision controls fail closed.

## Pinned-container validation

Image: `issue2679-map01-runtime:20260921-pinned`, digest `sha256:029e1867aeb843f2d63080343bfbb61540b64852ce00d4d99ec0be51796a093e`.

Run used `--network none --read-only`, read-only mounts for the model and predecessor calibration fixture, and `--entrypoint python` to bypass the image's MAP01 runner entrypoint. Result: **PASS, 5/5**. No model, GPU, game, or input call occurred.

## Gate boundary / next step

This is a contract model, not a test of `ObservableSignalPolicyMonitor`, the adapter, or `final_action_admission_v2`; it does not yet satisfy Issue #4536's explicitly typed captured hard-invalidation receipt or prove that the real stale turn is stopped before Executor input. Therefore no formal allocation is authorized by this result. Next locally test the actual production boundary with a captured typed receipt and retained calibration; only if that gate passes should the one fresh seed/path preflight and formal allocation be considered under #4536.
