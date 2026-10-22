# Spatial coordinate uncertainty and GUI hit-region risk

## Issue #8881

**Status:** Open, unverified robotics-to-GUI evaluation-method proposal. No current click-mislocalization defect, calibrated risk estimate, live input, or action authority is claimed.

**Idea.** Given an estimated coordinate distribution and crop/scale/offset transforms, compute how much probability mass lands inside the authorized target, in forbidden neighboring hitboxes, or outside all candidates. Compare point-estimate admission, worst-case uncertainty sets, and a probability-mass diagnostic that may choose fresh reacquisition or abstention. The proposed first rung uses exact discrete pixel distributions, with multimodal/misspecified-estimator tests kept separate from any Gaussian assumptions.

Cases include correlated and anisotropic error, multimodal error, stale crop origin, transform rounding, edge and overlapping hitboxes, and candidate-family growth. Probability mass may help decide when to gather more evidence; it cannot turn a stale or semantically ambiguous target into authority. The robotics chance-constraint literature motivates geometry under uncertainty but does not establish GUI target identity or safe action.

**Current evidence:** No implementation or result reported for #8881. The idea explicitly proposes a no-live-action finite model before any later rung. See [Issue #8881](https://github.com/Unjuno/agent-interface/issues/8881).

## Related but distinct evidence: #6684

Issue #6684's separate finite relational-coordinate study was integrated by [PR #6701](https://github.com/Unjuno/agent-interface/pull/6701). Its allocation-06 result is `PASS_METHOD_SCOPED`: one candidate and one independent exhaustive auditor, 9 cases / 98,414 concrete states, zero false admissions. Three exact-safe common-mode cases reduced false UNKNOWN from 3 with BOX bounds to 0 with relational bounds; independent-error controls showed no decision differences.

This result concerns authored integer-pixel relational bounds, not a probability distribution over target/decoy hit regions. It is not click-risk calibration, GUI/runtime behavior, or action-authority evidence. Earlier STOPs remain preserved. See [Issue #6684](https://github.com/Unjuno/agent-interface/issues/6684) and the [retained report](../../research/analysis/relational_coordinate_bounds_6684_t0_20261002/REPORT.md).

## Neighboring contracts

Cached points still require fresh current-image revalidation (#663); candidate multiplicity (#6204) concerns semantic score selection rather than geometric landing probability; patch informativeness and edge-grounded points (#3463/#3465) ask different questions. A future study must keep target identity and effect verification independent from the geometry estimator.
