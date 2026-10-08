# Live `authority_ended` two-dispatch MAP01 gate v1

Status: **PASS_LIVE_TWO_DISPATCH** for two fresh model-free ViZDoom/X11 sessions. This is a live control-semantics result, not gameplay efficacy, model/planner efficacy, hard-real-time qualification, or production promotion.

## Question

The retained transcript study (`authority_ended_two_dispatch_v1`) showed that a scheduled `authority_ended` receipt plus valid post-release evidence can open only a one-use replan opportunity, and that a later current observation plus ordinary revalidation must precede another execution.

This block changes one thing only: **replace the transcript second execution with a real second X11/ViZDoom physical key action.**

The first program's authority must not leak into the second. A deliberately stale control must send no second program at all.

## Runtime / provenance

- immutable runtime source bundle: `9e6d5ecdbb5440fd5df1883161f2c63b2c3bb245`;
- ViZDoom 1.3.0 / Freedoom MAP01, `map01-threat-contact-v2`, skill 1;
- ASYNC_SPECTATOR, 35 Hz;
- CPython 3.13.5 / Linux 6.18.44 / shared Intel Xeon Platinum 8573C host; CPU frequency not pinned;
- private Xvfb/Openbox session per arm;
- same seed `994100` for both formal arms;
- zero model calls;
- no retry of either formal arm.

The live harness used exact local frozen copies of the authority-ended bridge and one-use sequence gate. Those local source bytes are retained with this result. They implement the same contract as the subsequently merged transcript gate, but byte identity is not asserted.

## Frozen design

Both arms first execute:

1. initial exact observation;
2. `Shift_L` hold requested for 2000 ms;
3. independent input-owner authority deadline at 600 ms;
4. expected `authority_ended` terminal with verified expired owner release;
5. exactly one passive post-authority observation, no old-tail resumption and no input-authority regrant.

### Valid arm

- open a one-use token bound to the post-authority observation sequence;
- submit an observe-only program;
- require its current sequence to be strictly greater than the token sequence;
- revalidate the token;
- consume the token once;
- only then submit a real second `Shift_L` hold for 80 ms;
- require ordinary Executor admission and verified empty release.

### Stale arm

- do not acquire a later observation;
- present `current_sequence == post_sequence`;
- require `stale` from the gate;
- send no second program.

## First formal outcome

Decision: **PASS_LIVE_TWO_DISPATCH**.

| Gate | valid arm | stale arm |
|---|---|---|
| first terminal | `authority_ended` | `authority_ended` |
| first expired release verified empty | PASS | PASS |
| post-authority sequence | 2 | 2 |
| current sequence at gate | 3 | 2 |
| gate | `revalidated` | `stale` |
| input admissions after first release and before second submit | **0** | **0** |
| second program sent | yes | **no** |
| second physical input admissions | **1** | **0** |
| second terminal | `completed` | n/a |
| second release verified empty | PASS | n/a |
| strict final independent scorer agreement | PASS | PASS |

In the valid arm, `post_first_release_input_admissions_observed=1` over the entire remaining episode because that count includes the **intended** second action. The causal gate is the narrower interval before the second submit, where the count is exactly zero.

### Timing observations

- valid first deadline -> verified empty: **1.509 ms**;
- valid first verified empty -> post-authority capture: **16.682 ms**;
- valid first verified empty -> second physical input admission: **188.817 ms**;
- stale first deadline -> verified empty: **0.655 ms**;
- stale first verified empty -> post-authority capture: **14.510 ms**.

These are two shared-host observations, not latency distributions or hard-real-time guarantees.

Both sessions ended alive with no MAP01 exit, zero deaths and zero kills. That is not a gameplay-efficacy result; the comparison key was chosen to test physical authority semantics.

## Retained construction failure

The first smoke harness attempted to read `owner-events.json` immediately after the first terminal. That file is written at session close, so the harness could not obtain an online release receipt there. No formal session was consumed. The harness was repaired to use the owner-release record already retained inside the terminal's `interruption.record`, then a corrected smoke passed before preregistered formal execution.

This is an attribution/harness repair, not a mechanism change.

## Independent audit

`audit_live_two_dispatch_v1.py` replays the retained result plus raw `events.jsonl`, owner/scorer receipts and checks:

- exact first `authority_ended` and verified expired release;
- one bounded no-authority post capture and zero tail revival;
- no post-release input before the valid second acceptance;
- exactly one admitted second physical action in the valid arm;
- no second submission/input in the stale arm;
- verified empty second release;
- five-field `score.json` agreement with the independent direct-final scorer sample.

The local audit passes.

## Evidence retention boundary

The valid arm retains a full compressed text bundle on GitHub containing the original `events.jsonl`, owner/scorer receipts, environment/source manifests and harness stderr with per-file SHA-256 values. The stale arm full raw bundle remains local only: two remote upload attempts produced byte counts that did not match the frozen local base64 file, so those malformed GitHub copies were deleted rather than called retained. GitHub instead retains an exact compact stale-arm extraction containing the first terminal/expired release/post-authority evidence, the empty post-release input set, the empty `second`-ID event set, terminal score/direct-final scorer sample and hashes of the original raw sources. `audit_retained_compact.py` audits the report's release/admission/scorer claims using GitHub-retained evidence only.

PNG/AIT/setup-screen binaries remain local-only and are not needed for these claims.

## H / T / D / C / U

**H.** A sequence-bound one-use replan gate can separate two *live* input-authority epochs: ending the first authority does not authorize a second physical action; only later fresh evidence and new admission do.

**T.** Two fresh real ViZDoom/X11 sessions at the same fixture/seed: one valid later-observation path and one deliberately stale control. One 80 ms second physical hold only in the valid arm. Zero model calls; no formal retries.

**D.** **PASS_LIVE_TWO_DISPATCH** because every hard gate passed: valid second actuation occurs only after a strictly newer observation and revalidation, stale control emits no second submit/input, all releases are verified empty, and independent terminal scoring agrees.

**C.** The harness serializes the replan logic after the first terminal; it does not yet test a remote planner racing on the earlier `authority_ended` event while the post-authority capture is still pending. The second key is semantically inert for gameplay and one seed cannot establish reliability.

**U.** One valid + one stale formal session, one fixture, one host, unpinned frequency, no frontier model, no useful gameplay target, no cross-domain transfer. Scheduler/capture timing and event-delivery races remain open.

## Next smallest experiment

Do not add a model yet. Exercise the **real delivery race** that still remains: when the live `authority_ended` event is delivered before the post-authority observation/terminal is assembled, attempt to open the next-dispatch path immediately. It must fail closed and admit zero input. After the valid post-authority receipt arrives, the same session may obtain one later observation and admit exactly one new physical action through the existing gate. Change no policy semantics beyond this timing/order exposure.
