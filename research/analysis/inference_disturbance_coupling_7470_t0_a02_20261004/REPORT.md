# Issue #7470 T0 A02 — PASS_METHOD_SCOPED

## Decision

The frozen finite method test passed. All 24 assignments of the exact latency multiset `{1,2,3,4}` to the exact disturbance sequence `{0,1,2,3}` were evaluated in both the null and planted-interaction plants (48 trajectories total). The independent auditor reconstructed every event/trajectory and rejected all three preregistered mutations.

## Observed finite result

- Every assignment retained the same latency and disturbance marginals, total latency/termination tick `10`, and stale-cover occupancy `10` ticks.
- Null plant: state trace `[0,0,1,3]`, peak `3`, and zero event-steps outside the declared envelope for all 24 assignments.
- Planted interaction: rank-aligned peak state `8.0`, with one event-step outside envelope `x<=6`; rank-reversed peak `5.5`, with zero outside. Severity-weighted stale exposure was `20` versus `10`, respectively. Both used identical latency and disturbance marginals.
- The raw rows also retain per-event inference completion time and the toy oracle's `useful_fresh_action_at_tick`; these are synthetic event-clock outputs, not measured wall-clock or real-agent utility.

## Formal record and audit

- Candidate: one isolated-mode invocation, exit 0; `CANDIDATE_COMPLETE pairings=24 trajectories=48`.
- Auditor: one independent raw-only invocation after candidate exit 0, exit 0; `PASS_METHOD_SCOPED`, 48/48 trajectories reconstructed, 3/3 mutations rejected.
- Candidate JSON SHA-256: `8438aad90260f91a29e4f7fa8aa16e554f0d6c881e5bf0179441ce8c3f98ded8`.
- Freeze SHA-256: `261c3d92f08065313826e262c85ba376247669ad24bf6deff36db1ba878f5d29`.
- A01 remains the immutable pre-candidate `STOP_MAIN_ADVANCED_PRELAUNCH` (#5976972848); its candidate/auditor counts remain 0/0.

## Scope and limits

This confirms only that the finite analysis harness detects its intentionally planted latency×severity interaction while preserving a no-interaction control. The interaction term was specified by construction, so this is not evidence that real inference latency and GUI/game disturbances are coupled, nor that this state, action, event-clock, or envelope represents a real system. No population probability, causal runtime effect, safety bound, model quality, GUI/game result, user benefit, or deployment threshold is established. T1 remains conditional on retained traces with source-bound latency, disturbance, cover, state, and outcome provenance; absent any of these, retain `HOLD_NO_ELIGIBLE_TRACE`.

## Environment

Host-only CPython standard library on macOS arm64. No container, model, GUI, game, network, external actuation, GPU, or user data was used. The Issue specifies this T0 as a CPU-only finite simulator and does not require container isolation. No isolation claim is made.
