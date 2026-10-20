# Rotation-invariant features for relative-view control

**Status: unverified transfer; Issues #31 and #8636 remain open.** The five
retained attempts are scoped synthetic CPU studies. No result establishes a
usable feature method, game-camera control, GUI behavior, model benefit, task
success, safety, latency, or transfer from robotic visual servoing.

## Question and decision boundary

Issue [#31](https://github.com/Unjuno/agent-interface/issues/31) asks whether
an agent can control relative viewpoint in a 3D environment instead of treating
every view as an unrelated screenshot. Successor
[#8636](https://github.com/Unjuno/agent-interface/issues/8636) narrows one
question: can rotation-invariant features from target-relative image points
support bounded view alignment under an explicit projection/landmark model?
The cited three-point visual-servoing paper studies a robot arm under spherical
projection; its assumptions do not establish robustness for game or GUI
screenshots, unknown landmarks, or task success. Image-derived features remain
separate from explicit ViewState and do not replace it generally.

The decisive comparison is a bounded alignment task with a simple image-space
baseline and an explicit ViewState oracle. Measure target-relative error and
false alignment under rotations, occlusion, and near-singular features. The
oracle must not depend on the image detector being evaluated; any abstention,
feature-loss, or failure reason must be specified identically in candidate and
independent auditor. Do not pool the previous seeded runs or relabel their
first outcomes.

## Retained attempts

| Packet | First result and evidence boundary |
|---|---|
| A01, [PR #8711](https://github.com/Unjuno/agent-interface/pull/8711) | Candidate completed 360 synthetic trials; its single auditor stopped on a focal-shift YIELD that the protocol permits as calibration-stress abstention but the frozen auditor accepts only for feature-loss faults. `HOLD_UNCERTAIN`; construction 10/10. No method or hypothesis conclusion. |
| A02, [PR #8746](https://github.com/Unjuno/agent-interface/pull/8746) and audit-only [PR #8748](https://github.com/Unjuno/agent-interface/pull/8748) | The candidate completed 360 trials, but the auditor stopped before summary at a status-decision mismatch. The freeze names Python 3.12.13 while formal commands used 3.14.5. The separate audit-only replay found the frozen oracle expected STOP while the runner emits the pose action through step 12. Preserve both first outcomes; neither adjudicates the hypothesis. |
| A03, merged successor [PR #9236](https://github.com/Unjuno/agent-interface/pull/9236) to closed original [PR #8840](https://github.com/Unjuno/agent-interface/pull/8840) | Candidate completed 360 trials (exit 0); the auditor exited 1 before summary because the focal-stress YIELD reason was `feature shape changed` while the auditor expected `shape changed`. `HOLD_UNCERTAIN`; no method conclusion. The 2,231-file first-outcome archive matches every path, byte count, and SHA-256 in its internal manifest (63,489,719 bytes); the package's 17-member Git-blob checksum manifest also matches. The successor repairs the generated analysis index only; the candidate and auditor were not rerun. |
| A04, [retained packet](../../research/analysis/relative_view_rotation_features_8636_t0_a04_20261012/A04-RESULT.md) (original [PR #8844](https://github.com/Unjuno/agent-interface/pull/8844)) | Candidate completed 360 trials; the auditor stopped on `feature_loss-30090-viewstate_oracle`, step 0. Image detection ran before the privileged ViewState oracle, so near-singular image evidence made the oracle yield. `HOLD_UNCERTAIN`; the 2,198-file archive and 14/14 construction checks are retained. Read-only custody recheck verified 2,198/2,198 archive members; the recorded manifest SHA corresponds to its CRLF representation, while the canonical LF Git blob has a different hash. See the [custody recheck](../../research/analysis/relative_view_rotation_features_8636_t0_a04_20261012/CUSTODY_RECHECK.md). |
| A05 construction, merged [PR #9238](https://github.com/Unjuno/agent-interface/pull/9238), supersedes [PR #8861](https://github.com/Unjuno/agent-interface/pull/8861) | Reapplied to a temporary copy on current main and reran the guarded verifier: four focused regressions plus 13 applicable A04 construction tests pass in normal and optimized Python. The oracle arm bypasses image detection while the image arm still yields. The pinned A04 source hashes matched; no formal candidate or full auditor was rerun. A04 remains `HOLD_UNCERTAIN`. |

## Next finite discriminator

The A05 repair is now locally reproduced on current main, but it is only a
temporary-source construction patch. Next, independently reconcile the A01–A04
first-failure predicates with the patched runner and auditor, including focal
stress, feature loss, oracle bypass, and one pinned interpreter. Only after the
decision contract and all construction checks agree should a new allocation be
requested and frozen; all prior allocations/audits are consumed. A positive
synthetic result would still require separate game-camera and task-effect
evidence before transfer.
