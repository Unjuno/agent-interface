# Inkscape cross-domain `authority_ended` ABI v2

Status: **PASS_ABI_ADAPTER_V2** in one fresh model-free Inkscape/X11 session after a 15/15 offline contract matrix. A preceding v1 normalization candidate was rejected before live execution because it misreported two actual post-release captures as `captures=1`.

## Question

The retained Inkscape expiry-observation path already verifies release, stops the unfinished input tail, and performs two passive post-release captures. The newer MAP01 `authority_ended` caller contract additionally requires an explicit post-authority observation lifecycle and previously assumed exactly one capture.

Can the old Inkscape mechanics satisfy a **truthful** cross-domain contract without changing motor behavior or its two-capture observation policy?

## Retained construction failure

`post_authority_normalize_v1` attempted to expose only the latest observation as `captures=1` while separately noting `source_captures=2`. That is semantically wrong because the bridge field denotes actual bounded post-authority capture count, not merely the number selected for planner presentation.

Disposition: **REJECT_BEFORE_LIVE_AS_SEMANTIC_MISREPRESENTATION**. No formal live allocation was consumed.

## v2 contract

Bridge v2 preserves the existing one-capture Doom receipt unchanged and adds one bounded representation only:

- `captures=2` is the actual count;
- `sequences=[s1,s2]` must contain exactly two strictly increasing sequences;
- `sequence=s2` and `selection_rule=latest` prove which actual observation is selected;
- three or more captures are not accepted without a new contract;
- all previous verified-release, zero-input, no-tail, sequence-advanced, error-free and lifecycle-deadline checks remain.

The Inkscape runtime candidate changes **only status/evidence ABI** for scheduled expiry. It keeps the old `post_release_observation_v2.collect` behavior unchanged (two 80 ms-spaced passive snapshots), records a separate 400 ms observation-lifecycle deadline, and exposes the latest actual sequence. Focus/surface/cancel/release-failure paths are not relabelled.

## Offline matrix

15/15 PASS:

- existing retained single-capture Doom receipt accepted;
- honest two-capture latest-selection receipt accepted;
- missing sequence list, count mismatch, non-latest selection, unproven 3-capture, late lifecycle and legacy `expired` all reject;
- fake scheduled expiry preserves two captures and bridges successfully;
- release failure, focus decision and cancellation are not upgraded;
- deliberately slow two-capture observation marks lifecycle late and bridge rejects.

## Live formal block

Construction smoke seed 994599 passed and is excluded. Formal seed **994600**, one session, no retry, zero model calls.

Runtime: Inkscape under private Xvfb/Openbox; `Shift_L` hold requested 1500 ms under a 500 ms authority deadline, followed by tail text `999` which must never execute.

First formal outcome: **PASS_ABI_ADAPTER_V2**.

- terminal: `authority_ended`, `legacy_terminal_status=expired`;
- expired owner release verified with empty keys/buttons;
- tail text step never starts;
- unchanged legacy post-release collector: **2 captures**, sequences **[10, 11]**;
- normalized post-authority evidence: `captures=2`, `sequences=[10,11]`, selected sequence **11**, `selection_rule=latest`;
- independent lifecycle deadline: snapshot finished inside budget with **177.959 ms** slack;
- post-release input admissions: **0**; input between `input_stopped` and terminal: **0**;
- bridge v2 result: `safe_yield / authority_unavailable`;
- saved SVG remains x=50, y=50, width=40, height=30; this is expected interruption, **not editing-task success**;
- driver exits 0 and socket/cancel-socket are removed.

### Timing observations

- authority deadline -> verified empty: **0.670 ms**;
- verified empty -> first post-release capture: **89.518 ms**;
- verified empty -> latest selected capture: **215.136 ms**;
- verified empty -> normalized post-authority evidence finished: **222.008 ms**.

These are one shared-host session, not distributions or hard-real-time guarantees.

## H / T / D / C / U

**H.** Cross-domain post-authority evidence can generalize from one to two bounded captures without hiding actual observation work, if actual sequences and latest-selection provenance are explicit and the same release/lifecycle safety gates remain.

**T.** One 15-case offline contract/fake-executor matrix followed by one fresh real Inkscape/X11 formal session at frozen seed 994600. Zero model calls and no formal retry.

**D.** **PASS_ABI_ADAPTER_V2.** Every frozen gate passes. The v1 representation failure remains retained and is not relabelled as success.

**C.** Bridge v2 currently supports only one or two captures. This is deliberate evidence-boundedness, not a universal cardinality limit. The 400 ms lifecycle is a candidate bound, not yet cross-host calibrated. The old two-capture collector itself may be slower than a future one-capture design, but this experiment does not compare policies.

**U.** n=1 live session, one application/layout/host, no model, no positive editing effect, no durable-submit composition yet. Visual frame binaries remain local; the retained compact evidence contains terminal/input/source identities and independent SVG result.

## Next smallest experiment

Now that Inkscape can emit the same honest authority-ended ABI, compose **only** the already-retained durable-token + durable-submit ordering in this same application. Do not alter motor/capture policy again. One live crash-after-send path with separate-process read-only reconciliation is the highest-information next step.
