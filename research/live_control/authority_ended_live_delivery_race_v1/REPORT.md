# Live `authority_ended` delivery-race gate v1

Status: **PASS_RACE_GATE** for one fresh model-free ViZDoom/X11 session. This is control/lifecycle evidence only; no gameplay-efficacy, frontier-model, population-reliability, or hard-real-time claim.

## Question

The retained live two-dispatch block proved that a stale second dispatch sends zero input and that a later fresh observation can admit one new physical action. That block waited for the first terminal, which is emitted only after the post-authority snapshot finishes.

The remaining timing ambiguity was narrower: the runtime emits an earlier live `authority_ended` event after verified release but **before** the post-authority observation is assembled. Can a caller observing that early event accidentally open the next input epoch too soon?

This experiment changes only that delivery ordering exposure.

## Runtime / freeze

- immutable runtime source base: `9e6d5ecdbb5440fd5df1883161f2c63b2c3bb245`;
- ViZDoom 1.3.0 / Freedoom MAP01 / `map01-threat-contact-v2`, skill 1, ASYNC_SPECTATOR 35 Hz;
- CPython 3.13.5 / Linux 6.18.44 / shared Intel Xeon Platinum 8573C; frequency unpinned;
- private Xvfb/Openbox;
- seed `994200`;
- first `Shift_L`: requested 2000 ms, independent authority deadline 600 ms;
- second `Shift_L`: 80 ms, permitted only after the normal post-release and later-observation path;
- zero model calls; one formal session; zero formal retries.

Preregistration, harness and gate/bridge source hashes were frozen before the formal session.

## Mechanism / hard gate

At the first live `authority_ended` event:

1. the event already contains a verified `expired` owner-release record and empty physical keys/buttons;
2. it explicitly grants no input authority and reports zero old-tail resumption;
3. it **does not yet contain** the post-authority observation.

The harness constructs a caller receipt from exactly those available facts, with `post_authority=None`, and attempts `open_replan_token` immediately. It must reject specifically with `post-authority observation required`. No submit/input is issued by this attempted early transition.

Only after the first terminal contains the valid post-authority observation may the harness open a token, submit one observe-only program, require a strictly newer sequence, revalidate and consume the one-use token, and submit one new physical 80 ms action.

## First formal outcome

Decision: **PASS_RACE_GATE**.

- early event release: verified, reason `expired`, keys/buttons empty;
- early gate: **rejected** with `post-authority observation required`;
- input admissions after first verified expiry release through the early rejection: **0**;
- input admissions after first release through the first terminal: **0**;
- first terminal: `authority_ended`, post sequence **2**, one bounded passive capture, no authority grant, no tail resumption;
- observe-only: completed, current sequence **3**;
- later gate: `revalidated`;
- input admissions after first release before second submit: **0**;
- second physical input admissions: **1**;
- second terminal: `completed`, verified empty release;
- strict five-field final independent scorer agreement: **PASS**.

The session ended alive, with zero kills/deaths and no MAP01 exit. The key is semantically inert here; this is not gameplay-efficacy evidence.

## Measured race window

| Interval | observed |
|---|---:|
| first deadline → verified empty | 0.845 ms |
| verified empty → early `authority_ended` emit | 0.221 ms |
| early event emit → first terminal emit | **65.626 ms** |
| verified empty → post-authority snapshot finished | 65.840 ms |
| first terminal emit → second program accepted | 85.714 ms |
| first verified empty → second physical input admission | 152.036 ms |

The ~65.6 ms early-event-to-terminal interval is a real observed window in this session during which release is already verified but the evidence required to reconsider has not arrived. These are single shared-host observations, not latency distributions or real-time guarantees.

## Independent audit / retained evidence

`audit_live_authority_race_v1.py` replays the raw `events.jsonl` and scorer evidence, reconstructs the early caller-visible receipt from the actual `authority_ended` event, reruns the gate rejection, verifies zero pre-second input, verifies the one later second input and release, and compares `score.json` against the independent direct-final scorer sample. The audit passes.

The GitHub namespace retains the raw text evidence as one deterministic gzip/base64 bundle with per-source SHA-256 identities. PNG/AIT visual binaries remain local-only; they are not needed for the ordering/release/admission/scorer claims made here.

## H / T / D / C / U

**H.** A verified release event is still insufficient to reopen semantic/input progression when the required post-authority evidence has not yet arrived; the caller gate should treat that interval as fail-closed.

**T.** One fresh real ViZDoom/X11 session. Expose the actual early event, attempt one local next-dispatch gate transition immediately, then continue the same session through the normal terminal/post-observation/later-observation path and one new 80 ms physical action. Zero retry.

**D.** **PASS_RACE_GATE** because the early transition was rejected for the missing post-authority observation with zero input, while the later evidence path admitted exactly one newly authorized action and all release/scorer gates passed.

**C.** The caller-side gate invocation is local and synchronous; a real remote planner/network client may introduce different delivery and retry races. The experiment does not test duplicate messages, delayed old terminal delivery, or planner-generated semantics.

**U.** n=1, one fixture/key/host, no model, no useful task effect. The measured 65.6 ms window may vary substantially with capture/artifact work and scheduler load.

## Next smallest experiment

Do **not** add a model yet. Test one **duplicate/out-of-order delivery** condition model-free: after a successful later replan token has been consumed for the second action, inject the previously valid early `authority_ended` event and first terminal again in reversed/delayed order. Neither duplicate may reopen a token or admit input. If that passes, the remaining local lifecycle ambiguity is small enough to justify one bounded model-in-loop handoff study.
