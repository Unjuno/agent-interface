# Issue #8636 T0 A02 — corrected focal-shift audit taxonomy

## Why A02 is a new allocation

A01 is preserved as `HOLD_UNCERTAIN`; its candidate produced 360 trials, but its auditor stopped at the first focal-shift `YIELD / feature shape changed` because the frozen expected-YIELD taxonomy only included feature-loss faults. A02 does not retroactively reinterpret A01. It corrects that specific audit contract, freezes a new package on current main, and uses a new deterministic seed set (30030–30059 in each stratum). Candidate, equations, thresholds, actuator model, observation cadence, outcome criteria, and primary hypothesis remain fixed. No threshold is relaxed.

The correction is explicit: in focal-shift stress rows, either image-only arm may yield only when the independent auditor reconstructs the same frozen pairwise-shape gate failure and the exact reason. Such rows remain stress-stratum target loss / UNKNOWN_YIELD and are reported separately. They do not enter the primary H metric and do not count as a feature-loss control. Unexpected focal yields still fail audit. The three explicit feature-loss arms and all primary comparisons retain A01 gates.

## H / T / D / C / U

**H:** On fixed-position synthetic three-landmark views with held-out yaw/pitch starts and a fixed nominal projection, the spherical feature controller reaches the same exact terminal-view criterion with no greater target-loss or action-bound violation rate than raw normalized coordinates and reduces median corrections by at least 20% on rotation-only and combined-rotation pairs. Focal variation and feature-loss strata are separate stress findings.

**T:** Deterministic CPU-only fixtures: 30 paired held-out seeds in each of four strata, new seeds 30030–30059. Conditions, candidate equations, renderer, detector, actuator, and observation schedule match A01. Compare raw normalized point-coordinate correction, spherical distance/orientation-feature correction, and hidden-pose oracle upper reference. Preserve frames, events, action decisions, scorer truth, and synthetic neutral-release receipts. The auditor independently reconstructs the renderer, features, actions, trajectories, and scoring from raw output and sealed truth.

**D:** `PASS_METHOD_SCOPED` requires 120 paired fixtures / 360 arm trials; exact source/frame/event custody; equal arm budgets; zero independent replay errors; every corruption control rejected; all eight invalid feature-loss controls abstain in both image arms (54 trials total); radial range variation preserves the image; actions stay within the envelope; and every trial retains a neutral terminal release receipt. In focal-shift rows, an image-arm YIELD is accepted only if independently reconstructed from the frozen 0.09-rad pairwise-shape gate with exact `yield_reason`; it is retained as a stress outcome, not silently recoded as success. No other unexpected YIELD is allowed. `H_SUPPORTED_SCOPED` additionally requires the frozen primary success/loss and ≥20% median correction-reduction gates. A valid run missing that threshold is `H_FAIL_SCOPED`; integrity or unexplained decision mismatch is `HOLD_UNCERTAIN`.

**C:** Raw coordinates with a fixed image Jacobian may already capture the small yaw/pitch task; feature extraction can add ambiguity; a focal-shift abstention can be prudent but reduce usefulness outside calibration. Explicit ViewState remains a simpler upper reference where available.

**U:** Authored synthetic rays, fixed camera center in primary strata, known nominal focal length, deterministic 2-D action mapping, and synthetic release receipts only. No screenshot tracker, live GUI/game, task effect, physical release, human benefit, general navigation, production safety, or product result is established.

## Fixed inputs and execution

- Base current main: `ffe5292b3164a3eb7e2b5d18eaadcbafdcd2b385`.
- Preserved predecessor: #8636 A01 result commit `48135041a13c0988cf2d254dc5680f611063d10e`, with its original A01 freeze and first outcome unchanged.
- A02 allocation: `UNJUNO-8636-ROTATION-FEATURES-T0-A02-20261009`.
- Seeds: 30030–30059 in each of pure_yaw, combined_rotation, focal_shift, and feature_loss; three arms per seed.
- 96×96 binary P6 PPM frames, nominal focal length 48 px, max 12 relative-look actions per arm, per-axis action limit 0.08 rad, gain 0.72, stop tolerance 0.015 rad, terminal tolerance 0.025 rad, pairwise-shape tolerance 0.09 rad, two-bearing condition floor 0.08.
- Feature-loss faults remain: hidden landmark, identity swap, moving landmark, near-singular geometry, low texture, camera translation, stale generation, viewport resize, and radial range variation. Eight invalid controls require image-arm abstention; radial range variation is a perspective-projection null.
- Commands: one `python3 -B runner.py --output results/a02-outcome`, then one `python3 -B auditor.py --output results/a02-outcome --result results/a02-outcome/audit.json`. No retry, rerun, or threshold tuning.
- Host CPU, local single-process Python; no model, GUI, OS input, human, GPU, container, Docker/OrbStack, WSL, or external service.
