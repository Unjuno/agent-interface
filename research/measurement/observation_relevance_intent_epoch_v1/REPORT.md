# #1645 O3 intent-epoch-bound relevance gating — retained formal result

Task: `OBSERVATION-GATING-O3-INTENT-EPOCH-BINDING-20260918-001`

Decision: **`PASS_O3_INTENT_EPOCH_BINDING_SCOPED`**.

## Question

#1583 established that relevant-region suppression must reject stale relevance generations. That does not cover a separate asynchronous gap: the semantic instruction/intent can change before a new relevance map is published. During that interval the old relevance generation may still be numerically current.

This successor tests whether relevance receipts need an additional runtime-owned intent/currentness binding. It does not consume #1635, which separately owns the private-X11 transfer of #1583.

## Analytical necessity witness

Let old intent `I1` use relevant set `A`. Let new intent `I2` require tile `x`, with `x ∉ A`. Assume intent switch may occur before the new relevance publication.

A relevance-only gate sees the same tuple immediately before and immediately after intent switch:

`(scope, relevance_generation=g, receipt_relevance=A, changed={x}, critical={})`.

In world W0 (`I1` still active), useful O3 gating may suppress `x`. In world W1 (`I2` active, relevance publication lagging), safety requires forwarding `x`. A deterministic function of the relevance-only tuple must produce the same output in both worlds. `SUPPRESS` violates W1 safety; `FORWARD` gives up the nontrivial W0 suppression. Therefore useful suppression + W1 safety requires either an additional intent/currentness discriminator or atomic intent+relevance publication.

The independent `ANALYTIC_VERIFY.py` enumerates the two possible deterministic outputs for this identical input and confirms neither satisfies both obligations.

## Candidate

The candidate adds one factor only: runtime-owned `intent_epoch`.

- `SWITCH_INTENT(new_id)` increments the epoch immediately when the intent changes.
- Each relevance receipt binds `{scope, relevance_generation, intent_epoch, relevant_tiles}`.
- Suppression requires both relevance generation and intent epoch to match current runtime state.
- Intent-epoch mismatch fails open to `FORWARD_FULL_CURRENT / STALE_INTENT_EPOCH`.
- A fresh receipt for the new intent restores normal relevance suppression.
- This recovery works even when the new intent uses the same ROI set and relevance generation therefore does not increment.

## Construction

Construction was `PASS_CONSTRUCTION_ELIGIBLE`.

Key directed outcomes:

- current irrelevant -> suppress;
- current relevant -> forward;
- intent switch with no new relevance publication -> candidate full-current fallback;
- relevance-generation-only comparator false-suppresses the hidden new-intent tile;
- same-ROI intent switch -> candidate conservatively forwards during the receipt gap;
- fresh post-switch changed ROI -> suppression recovers;
- fresh post-switch identical ROI -> suppression also recovers with unchanged relevance generation;
- critical change -> forward;
- missing/wrong/forged intent receipt -> fail open;
- malformed intent/tile controls reject; same-intent switch and exact duplicate receipt are no-ops.

Remote source bundle, manifest, construction summary and audit read back exactly. One construction archive Base64 transcription character was repaired before formal; scientific source was unchanged.

## Frozen formal

Exactly one deterministic formal invocation at seed `164220260918001`; reruns/replacements/tuning `0/0/0`.

| Family | Histories | Candidate result |
|---|---:|---|
| CURRENT_IRRELEVANT | 30,000 | suppressions 30,000 |
| CURRENT_RELEVANT | 30,000 | false suppressions 0 |
| INTENT_SWITCH_GAP_HIDDEN | 40,000 | false suppressions 0 |
| SAME_ROI_SWITCH_GAP | 25,000 | suppressions 0; full-current fallback |
| FRESH_POST_SWITCH_IRRELEVANT | 30,000 | suppressions 30,000 |
| FRESH_SAME_ROI_RECOVERY | 25,000 | suppressions 25,000 |
| CRITICAL_OUTSIDE | 20,000 | false suppressions 0 |
| MISSING_OR_WRONG_INTENT_RECEIPT | 10,000 | suppressions 0 |
| FORGED_INTENT_EPOCH | 10,000 | suppressions 0 |

Additional results:

- candidate/oracle full result+state mismatch: **0 / 220,000**;
- relevance-generation-only false suppressions in the hidden intent-switch discriminator: **40,000 / 40,000**;
- candidate hidden intent-gap false suppressions: **0 / 40,000**;
- same-ROI switch-gap candidate suppressions: **0 / 25,000**;
- fresh same-ROI recovery suppressions: **25,000 / 25,000**.

The same-ROI rows are important: semantic ownership can change without any ROI-coordinate change, so relevance-generation equality alone does not prove that the receipt belongs to the current intent. A fresh intent-bound receipt restores suppression without forcing a relevance-generation increment.

## Integrity

Frozen audit: PASS, errors `[]`; copied-result/analytic corruption controls **7/7 reject**.

Independent analytical verifier: PASS.

- formal result SHA-256: `ce726699c82701813d88c56132297c854642f64fdf986751f511ca158777cfe3`;
- retained compressed result SHA-256: `a6581380ca78d706074417e0deac506ac68ffacf3afdccac429ccbcfdf5b0ee5`;
- audit SHA-256: `17a845d90486c3070d7122ba4c18899ce777e90c28b96f377708e0e92038d770`;
- analytical verifier source SHA-256: `a8e10381b0c1503d624937a6a8b16c31fccdd5172b96485ab08916f41cbbf362`;
- analytical verifier result SHA-256: `1de0523692d3c419dff15557310aedd350c3c4c3afb522a6a9c97ab5e9cdc17c`;
- deterministic ledger SHA-256: `cbb1e6ab6251846dcaf04f98583ec186e52dd74dda4c547da4adfc999874a1a5`.

Postformal source hashes match the frozen source bundle exactly.

## Interpretation

For asynchronous instruction-conditioned observation, `relevance_generation` and `intent/currentness` answer different questions:

- relevance generation: is this ROI map the current version of the map?
- intent epoch: does this map still belong to the current semantic work item?

A safe O3 suppression contract therefore needs either both dimensions or a broader epoch that is atomically invalidated by intent change. Binding only to ROI coordinates/version can launder a semantically stale map through an intent transition.

## Boundary

Synthetic currentness semantics plus a finite indistinguishability witness only. No real GUI intent-switch timing, model relevance quality, task accuracy, image-token reduction, latency or production ABI claim. #1635 private-X11 transfer and #689/#671/#696 remain independently owned.
