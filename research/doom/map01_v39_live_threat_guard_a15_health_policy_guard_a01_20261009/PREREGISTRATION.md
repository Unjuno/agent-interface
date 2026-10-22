# A15 preregistration — live authored-cover health-policy boundary

Allocation: `map01-v39-live-threat-guard-a15-health-policy-guard-20261009`

Issue: #59

Owner: this Codex task, local Mac, exclusive use of the dedicated VM `issue59-live-v39-a01-20261009`; one invocation only.

Source: exact current-main V39/V15 closure, re-frozen at the A15 preregistration commit.

Model/input: first-party Codex app-server JSONL relay, `gpt-5.6-luna` low, no response delay, no manual gameplay, no request replay.

Fixture: `map01-threat-contact-v2`, MAP01 skill 1, Freedoom WAD SHA-256 `a8772e088847032510d97ba2312406a6998f21cbab44d4ff10696faa9c0ecd4b`, new seed `990625` (A14 used 990624).

## Hypothesis

A14 showed actual threat exposure, model-authored covers, and damage during inference, but under each active cover the fresh health stayed 5–8 points above its effective hard floor; the authored policy invalidation gate was therefore not exposed. With a new preselected seed, chosen before the run and not selected based on its outcome and an 18-decision cap, this episode tests whether a real enemy encounter drives fresh typed health below an active model-authored cover floor while frontier inference is pending, and whether cancellation/release precedes interruption followed by a fresh admitted plan within two decisions. This is a boundary-exposure test, not a causal efficacy comparison.

## Treatment and measurements

Run the unchanged current-main controller once from the fixed threat-contact fixture with seed 990625 and at most 18 decisions. Record for every model wait the active cover policy and its source observation, effective hard floor, health observations and sequences, cover renew/admission/cancel/release events, model completion/eligibility, per-key release custody, fresh follow-up decisions, independent scorer feedback, ammo/progress, and terminal outcome. Classify policy hard-minimum guards using the frozen `audit_recovery_censoring.py` predicate. Track action-validity max-decrease rejections separately; they are not policy hard-minimum triggers.

## Decision rules

- **Guard exposed:** a matching active authored-cover policy receipt reports health `HARD_INVALIDATED` below its hard minimum during the episode.
- **Scoped recovery pass:** at least one exposed guard is followed within two later decisions by a fresh-sequence, non-discarded plan, with matching cancel and verified-empty release custody; no stale dependent action is admitted.
- **HOLD / unexposed:** no policy hard-minimum guard occurs, or fewer than two later decisions are available. This does not imply the monitor failed.
- **FAIL / STOP:** exact source/runtime provenance or input-custody safety fails, or the controller/harness reports a fatal failure. Preserve the first result; do not retry.

The episode is independently audited. Do not promote the result to task success, causal survival benefit, general reliability, hardware key-state proof, game-consumption proof, or Issue #59 completion. Issue #59 remains open unless its other live threat-feedback and MAP01 outcome gates are met.

## Controls and stop rule

Freeze current-main SHA and ancestry, full runtime-source closure, controller/runner/auditor/tests, fixture and WAD hashes, app-server route, model/effort, seed, VM mapping, dependency versions, resource limits, output path, and audit criteria before launch. Require guest Python 3.12.3, ViZDoom 1.3.0, Pillow 12.3.0, python-xlib 0.33, openpyxl 3.1.5, Xvfb 1280x800, at least 2 GiB available guest RAM and `/tmp`, and no existing game/display process. Stop at the first of 18 decisions, death, MAP01 exit, runtime/model failure, 600 seconds of episode time, or the independent 900-second host-relay limit. No resume, retry, or in-place repair.
