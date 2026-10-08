# A16 preregistration — live authored-cover health-policy boundary

Allocation: `map01-v39-live-threat-guard-a16-health-guard-boundary-20261009`

Issue: #59

Owner: this Codex task, local Mac, exclusive use of the dedicated VM `issue59-live-v39-a01-20261009`; one invocation only.

Source: exact current main `57337e95ecbecf7e762c8ec8091472b79e8ad49f`, with the V39/V15 runtime closure checked against that commit by the frozen host runner.

Model/input: first-party Codex app-server JSONL relay, `gpt-5.6-luna` low, no response delay, no manual gameplay, no request replay.

Fixture: `map01-threat-contact-v2`, MAP01 skill 1, Freedoom WAD SHA-256 `a8772e088847032510d97ba2312406a6998f21cbab44d4ff10696faa9c0ecd4b`, preselected seed `990626` (A15 used 990625).

## Hypothesis

A15 reached 18 decisions with health 75–100 but did not cross any active authored-cover hard floor; its closest observed cover margin was five health points. A16 uses one new seed and a 24-decision cap, selected before the run and not based on outcome, to test whether current-main V39 invalidates an active cover when fresh threat-linked typed health crosses the model-authored floor during a pending model turn, and whether cancellation/release precedes interruption followed by a fresh admitted plan within two decisions. The runtime controller is unchanged. This is a boundary-exposure test, not a causal efficacy comparison.

## Treatment and measurements

Run the unchanged current-main controller once from the fixed threat-contact fixture with seed 990626 and at most 24 decisions. Record for every model wait the active cover policy and its source observation, effective hard floor, health observations and sequences, cover renew/admission/cancel/release events, model completion/eligibility, per-key release custody, fresh follow-up decisions, independent scorer feedback, ammo/progress, and terminal outcome. Classify policy hard-minimum guards using the frozen `audit_recovery_censoring.py` predicate. Track action-validity max-decrease rejections separately; they are not policy hard-minimum triggers.

## Decision rules

- **Guard exposed:** a matching active authored-cover policy receipt reports health `HARD_INVALIDATED` below its hard minimum during the episode.
- **Scoped recovery pass:** at least one exposed guard is followed within two later decisions by a fresh-sequence, non-discarded plan, with matching cancel and verified-empty release custody; no stale dependent action is admitted.
- **HOLD / unexposed:** no policy hard-minimum guard occurs, or fewer than two later decisions are available. This does not imply the monitor failed.
- **FAIL / STOP:** exact source/runtime provenance or input-custody safety fails, or the controller/harness reports a fatal failure. Preserve the first result; do not retry.

The episode is independently audited. Do not promote the result to task success, causal survival benefit, general reliability, hardware key-state proof, game-consumption proof, or Issue #59 completion. Issue #59 remains open unless its other live threat-feedback and MAP01 outcome gates are met.

## Controls and stop rule

Freeze current-main SHA and ancestry, full runtime-source closure, controller/runner/auditor/tests, fixture and WAD hashes, app-server route, model/effort, seed, VM mapping, dependency versions, resource limits, output path, and audit criteria before launch. Require guest Python 3.12.3, ViZDoom 1.3.0, Pillow 12.3.0, python-xlib 0.33, openpyxl 3.1.5, Xvfb 1280x800, at least 2 GiB available guest RAM and `/tmp`, and no existing game/display/controller/relay process. The frozen audit uses verified-empty terminal receipts to account for no-lease cancellations, requires token-matched owner releases for active leases, handles an absent controller-failure receipt as normal on clean exit, and rejects duplicate cancel or terminal identities. Focused mutation tests cover these boundaries before allocation. Stop at the first of 24 decisions, death, MAP01 exit, runtime/model failure, 600 seconds of episode time, or the independent 900-second host-relay limit. No resume, retry, or in-place repair.
