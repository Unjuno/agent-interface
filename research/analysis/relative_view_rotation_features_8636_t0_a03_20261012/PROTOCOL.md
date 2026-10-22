# Issue #8636 T0 A03 — preregistered protocol

## Allocation and delta

Allocation: `UNJUNO-8636-ROTATION-FEATURES-T0-A03-20261012`. Base: current `main` `f185a9059d485a4f8d5a65e9e7f6782897f67eae`.

A01 and A02 are consumed, preserved, and remain `HOLD_UNCERTAIN`; their inputs and outputs will not be rerun. A03 uses the new disjoint seed set 30060–30089. The A03 branch is based on current main, but the candidate algorithm is intentionally carried forward from the unmerged A02 package and is pinned by its own hash; A03 is a synthetic methods study, not a main-runtime integration claim. It keeps the candidate controller, renderer, fixtures, thresholds, outcome rules, and primary hypothesis fixed. The runner changes only allocation identity, output path, and seed range. The one auditor correction is justified by the A02 raw-only audit mismatch: the runner's `viewstate_oracle` arm emits the clamped pose correction on each step before step 12, even inside the image controllers' `0.015 rad` stop tolerance. The auditor had incorrectly applied that image-arm stop rule to the oracle. A03 adds a construction regression for this exact runner/auditor boundary. This does not revise either prior disposition.

## H / T / D / C / U

**H:** On fixed-position synthetic three-landmark views with held-out yaw/pitch starts and fixed nominal projection, the spherical-feature controller reaches the exact terminal-view criterion with no greater target-loss or action-bound violation rate than raw normalized point-coordinate control, while reducing median corrections by at least 20% on the preregistered rotation-only and combined-rotation pairs. Explicit ViewState is an upper-reference arm, not a candidate input.

**T:** Run the deterministic local analytic fixture once under the frozen CPython executable. Use 30 held-out seeds (30060–30089) in each of `pure_yaw`, `combined_rotation`, `focal_shift`, and `feature_loss`; shuffle arm order deterministically from seed and condition. This yields 120 paired seed-condition fixtures and 360 arm trials across `raw_pixels`, `spherical_features`, and `viewstate_oracle`. Candidate receives only generated P6 image bytes and public viewport/generation metadata; sealed pose truth is used only by the scorer and independent audit. Each arm has at most 12 relative-look corrections. Then run the independent raw-only auditor exactly once against the candidate's retained frames, events, truth, and receipts. Candidate invocation limit 1, auditor invocation limit 1, retry limit 0.

**D:** `PASS_METHOD_SCOPED` requires all 120 seed-condition pairs and all 360 arm trials; exact source/frame/event custody; equal action and observation budgets; zero independent replay errors; rejection of every frozen corruption control; abstention by both image arms on all eight invalid feature-loss controls (54 expected trials); radial range variation preserved as the projection-null stress; all actions within the `0.08 rad` per-axis bound; and a neutral terminal receipt in every trial. Focal-shift yields count as stress loss only when the auditor reconstructs the frozen pairwise-shape gate and exact reason. `H_SUPPORTED_SCOPED` additionally requires no worse exact terminal-view correctness or target-loss than raw pixels and at least 20% median correction reduction on the 60 primary pairs. A valid result missing the benefit gate is `H_FAIL_SCOPED`; any integrity or unexplained mismatch is `HOLD_UNCERTAIN`. No thresholds may change after execution.

**C:** Fixed raw-coordinate linearization may already solve this small yaw/pitch task. Feature extraction may add ambiguity; abstention under focal changes may prudently reduce usefulness. The reference arm may have privileged state and is not evidence that state is available in ordinary applications.

**U:** Authored analytic rays, fixed camera center in primary strata, known nominal focal length, deterministic 2-D actuator mapping, and synthetic neutral receipts only. No screenshot detector, real GUI/game, task effect, physical input release, model behavior, human benefit, general navigation, runtime safety, latency/token advantage, or portability is inferred.

## Frozen fixture details

- Frames: 96×96 binary P6 PPM, three color-coded landmarks; nominal focal length 48 pixels.
- Controller: gain 0.72; max 12 corrections; per-axis correction bound 0.08 rad; image-arm stop tolerance 0.015 rad; independent terminal tolerance 0.025 rad.
- Candidate geometry gate: pairwise spherical-shape tolerance 0.09 rad; two-bearing conditioning floor 0.08.
- Stress set: hidden landmark, identity swap, moving landmark, near-singular geometry, low texture, camera translation, stale frame, viewport resize, and radial range variation. The first eight are invalid and require abstention by both image arms; radial range variation is a projection-null control.
- Primary set: 30 pure-yaw plus 30 combined-rotation pairs; focal shift and feature loss are reported as separate stress strata.
- Audit controls: frozen source/order/staleness corruptions from the A02 audit package, replayed against A03 raw only. Candidate and audit processes remain separate.

## Exact commands and one-shot gate

`FREEZE.json` records the exact executable path and command argument arrays. Formal output path is new and must be absent or empty before candidate launch. Capture UTC start/end, stdout/stderr, exit code, file count, raw tree size, and archive hash for each process. Do not invoke again if the command status is unknown; inspect process/output state and preserve uncertainty. Once an invocation is recorded, no retry is allowed, including after an audit failure.

The experiment is a local deterministic CPU process and does not touch WSLc or the shared runtime lane. A03 is not authorized to start a GUI, game, model, OS input, container, or external service.
