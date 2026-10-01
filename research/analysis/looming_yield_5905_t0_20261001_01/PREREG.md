# Issue #5905 — T0 preregistration

Allocation: `LOOMING-YIELD-5905-T0-ISOLATED-ORB-20261001-01`
Frozen main: `906198f2b7b72db7d359921b50d9b6a22f503548`
Planned execution: isolated OrbStack Ubuntu 24.04 ARM64 guest; Docker daemon inside guest; candidate and auditor in separate network-disabled containers.
Candidate/auditor/retry budget: 1 / 1 / 0.

## H / T / D / C / U

**H.** In a finite, rendered perspective-approach fixture, a two-frame optical expansion time-to-contact (TTC) cue can request a simulated release before contact on eligible constant-speed centered approaches. It should abstain as `UNKNOWN` when source/track/time/geometry assumptions are observably violated. This experiment does not claim superiority over all alternative triggers.

**T.** Render deterministic grayscale PGM frames for four preregistered constant-speed approach cases spanning two initial scales and two speeds, plus seven assumption-boundary controls: lateral passage, common-mode camera zoom, animated target growth, occlusion, track identity swap, non-monotonic timestamps, and a nonlooming hazard. The positive-control geometry is `r(t)=K/z(t)`, `z(t)=z0-vt`, contact at `z=0`, with `K=512`, and frames are sampled every 0.1 s. Estimate `TTC = r_current / ((r_current-r_previous)/dt)` from measured raster area only when source/session and target-track identity match, timestamps increase, background scale is stable, target is centered/visible/unoccluded, and expansion is positive. Issue a cancel/release request when estimated TTC is at most 2.0 s. Simulated release latency is 0.10 s. Record all lossless frames, timestamps, metadata, estimate, decision, ground truth, and realized lead.

**D.** `METHOD_PASS_SCOPED` only if all four eligible approaches produce a release request at least 0.10 s before analytic contact, estimated TTC absolute error is at most 0.20 s at the decision frame, all seven violated-assumption controls return `UNKNOWN` without a `SAFE` label or release claim, and the independent raw-only auditor recomputes every frame commitment, estimate, decision, and metric without errors. Any eligible miss/late release, false `SAFE`, identity/time corruption accepted as valid, or audit mismatch is `FAIL_METHOD`. Container/setup failure before candidate is a typed `STOP_*`, not a scientific result.

**C.** This small fixture may favor its own estimator; two-frame finite differences are noisy and camera/target motion can be confounded. Immediate release or a simple event watcher may be safer and cheaper. No same-false-stop-allowance comparator or useful-progress endpoint is included in this first rung.

**U.** Synthetic perspective disks and explicit observability metadata are not a rendered game, GUI, agent policy, damage oracle, or live control loop. The finite scale/speed cases do not establish statistical generalization, real release latency, MAP01 survival, or any safety guarantee. Lack of a looming cue never means safe to continue.

## Source and output contract

The candidate only reads `fixture.json` and writes `raw.json`. The independent auditor only reads those two files and writes `audit.json`. Both execute in separate containers from the exact frozen image digest recorded in `FREEZE.json`; networking is disabled and resource limits are fixed. The raw record stores full PGM bytes as base64 plus SHA-256, so the rendered observations are losslessly retained. Seeds are not used; all coordinates and sequences are enumerated in the fixture.
