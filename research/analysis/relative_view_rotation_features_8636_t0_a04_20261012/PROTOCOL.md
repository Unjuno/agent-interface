# Issue #8636 T0 A04 — preregistered protocol

## Allocation and delta

Allocation: `UNJUNO-8636-ROTATION-FEATURES-T0-A04-20261012`. Base: current `main` `f185a9059d485a4f8d5a65e9e7f6782897f67eae`.

A01/A02/A03 are consumed, preserved, and retain their original `HOLD_UNCERTAIN` dispositions. No prior candidate, auditor, input, or output is rerun. A04 uses new disjoint seeds 30090–30119. Candidate, renderer, fixtures, thresholds, outcome rules, action budgets, and primary hypothesis are unchanged. The auditor includes both established corrections: (1) the ViewState oracle applies bounded corrections through step 11, independent of the image controllers' stop tolerance; (2) an independently reconstructed focal pairwise-shape abstention is recorded with the candidate's exact reason `feature shape changed`. A04's regression suite tests the A03 first mismatch from a fixed synthetic fixture; it does not execute or re-audit A03's raw data.

## H / T / D / C / U

**H:** On fixed-position synthetic three-landmark views with held-out yaw/pitch starts and fixed nominal projection, the spherical-feature controller reaches the exact terminal-view criterion with no greater target-loss or action-bound violation rate than raw normalized point-coordinate control, while reducing median corrections by at least 20% on the preregistered rotation-only and combined-rotation pairs. Explicit ViewState is an upper-reference arm, not a candidate input.

**T:** Run the deterministic local analytic fixture once under the frozen CPython executable. Use 30 held-out seeds (30090–30119) in each of `pure_yaw`, `combined_rotation`, `focal_shift`, and `feature_loss`; shuffle arm order deterministically from seed and condition. This yields 120 paired seed-condition fixtures and 360 arm trials across `raw_pixels`, `spherical_features`, and `viewstate_oracle`. Candidate receives only generated P6 image bytes and public viewport/generation metadata; sealed pose truth is used only by the scorer and independent audit. Each arm has at most 12 relative-look corrections. Then run the independent raw-only auditor exactly once against the candidate's retained frames, events, truth, and receipts. Candidate invocation limit 1, auditor invocation limit 1, retry limit 0.

**D:** `PASS_METHOD_SCOPED` requires all 120 seed-condition pairs and all 360 arm trials; exact source/frame/event custody; equal action and observation budgets; zero independent replay errors; rejection of every frozen corruption control; abstention by both image arms on all eight invalid feature-loss controls (54 expected trials); radial range variation preserved as the projection-null stress; all actions within the `0.08 rad` per-axis bound; and a neutral terminal receipt in every trial. Focal-shift yields count as stress loss only when the auditor reconstructs the frozen pairwise-shape gate and exact candidate reason `feature shape changed`. `H_SUPPORTED_SCOPED` additionally requires no worse exact terminal-view correctness or target-loss than raw pixels and at least 20% median correction reduction on the 60 primary pairs. A valid result missing the benefit gate is `H_FAIL_SCOPED`; any integrity or unexplained mismatch is `HOLD_UNCERTAIN`. No thresholds may change after execution.

**C:** Fixed raw-coordinate linearization may already solve this small yaw/pitch task. Feature extraction may add ambiguity; abstention under focal changes may prudently reduce usefulness. The reference arm may have privileged state and is not evidence that state is available in ordinary applications.

**U:** Authored analytic rays, fixed camera center in primary strata, known nominal focal length, deterministic 2-D actuator mapping, and synthetic neutral receipts only. No screenshot detector, real GUI/game, task effect, physical input release, model behavior, human benefit, general navigation, runtime safety, latency/token advantage, or portability is inferred.

## Frozen fixture details

- Frames: 96×96 binary P6 PPM, three color-coded landmarks; nominal focal length 48 pixels.
- Controller: gain 0.72; max 12 corrections; per-axis correction bound 0.08 rad; image-arm stop tolerance 0.015 rad; independent terminal tolerance 0.025 rad.
- Candidate geometry gate: pairwise spherical-shape tolerance 0.09 rad; two-bearing conditioning floor 0.08.
- Stress set: hidden landmark, identity swap, moving landmark, near-singular geometry, low texture, camera translation, stale frame, viewport resize, and radial range variation. The first eight are invalid and require abstention by both image arms; radial range variation is a projection-null control.
- Primary set: 30 pure-yaw plus 30 combined-rotation pairs; focal shift and feature loss are separate stress strata.
- Audit controls: frozen source/order/staleness corruptions and synthetic replay controls; candidate and auditor are separate processes.

## One-shot execution gate

`FREEZE.json` records the exact executable path and argument arrays. The formal output path `results/a04-outcome/` must be absent or empty before candidate launch. Capture UTC start/end, stdout/stderr, exit code, file count, raw tree size, and archive hash. Do not reissue a command with unknown status; inspect process/output state and preserve uncertainty. Once an invocation is recorded, no retry is allowed, including after an audit failure.

This is a local deterministic CPU experiment. No WSLc or shared runtime lane is used; no GUI, game, model, OS input, container, or external service is authorized.
