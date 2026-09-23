# MAP01 typed representation collision v1 — retained result

Task: `LOCAL-SYSTEM1-MAP01-TYPED-REPRESENTATION-COLLISION-20260917-001`
Issue: #937
Base: `048b76c917a2013b0bc3f3264466562d87860f0f`
Disposition: **PASS_TYPED_REPRESENTATION_COLLISION_REPLICATED_SCOPED**

## Question

Before allocating LINEAR/TREE/TINY-POLICY capacity for a real MAP01 residual decision, test whether the currently allowed typed textual state is sufficient for exact Astra-teacher imitation at all.

A finite sample can always be memorized by a lookup table, so rule length is not evidence that learning is necessary. The stronger prerequisite is functional consistency: identical allowed input signatures must not require distinct teacher labels.

## First formal outcome

Held-out source: retained `map01-soft-context-v31-live-01`, report Git blob `2aed2e7e3f58b4f8b013fc98c79482a4036225ae`.

- source rows: 8
- eligible completed/admitted teacher rows: 5
- exact prompt-signature groups among eligible rows: 4
- collision groups: **1**
- formal invocation count: 1
- reruns/replacements: 0
- independent audit: **PASS**, errors `[]`

The collision is iterations **1 and 2**. Their exact `prompt.txt` bytes are identical and both are Git blob `02edc59200629518b01080e16f7a4e132cda5c60`. The exact prompt says health 91, no preceding soft event, and no previous no-visible-effect action. Their structured eligible Astra outputs differ:

- iteration 1: `retreat_fire(short)`; next cover includes left/right strafe plus backward; validity `(critical_health_minimum=45, maximum_health_loss=8)`.
- iteration 2: `fire(pulse)`; next cover includes left/right strafe only; the same validity values.

Their model-image hashes are also distinct (`94756c...` versus `c5af6c...`), but image identity is diagnostic only and was never included in the formal input signature.

This independently replicates the development-known v30 pattern, where iterations 3 and 4 also had byte-identical typed prompts but distinct eligible actions. v30 was not included in the formal disposition.

## What the PASS proves — and what it does not

For the frozen exact typed textual signature `x`, the retained teacher data contain `x_1 = x_2` and normalized labels `y_1 != y_2`. Therefore no deterministic function `f(x)` can satisfy both `f(x_1)=y_1` and `f(x_2)=y_2` simultaneously. This applies equally to an exact rule, linear classifier, tree, deterministic neural network, or lookup table keyed only by that signature.

It does **not** prove that either teacher label is uniquely optimal, that visual pixels are the unique missing cause, that a stochastic policy would improve task success, or that a learned model is now justified. Astra saw a temporal sheet in addition to the textual prompt; the result is specifically a sufficiency failure of the frozen typed textual representation.

## H / T / D / C / U

**H:** a second retained MAP01 allocation contains at least one eligible exact-prompt group with distinct structured Astra execution labels.

**T:** source-first freeze exact prompt bytes, eligibility rule, label canonicalization and auditor; then one deterministic replay over v31 decisions 0–7. No training, model call, GUI/game action, authority grant, threshold search or image-derived signature feature.

**D:** PASS iff integrity passes and at least one eligible exact-prompt group has >=2 canonical labels. Observed one collision group; independent audit PASS.

**C:** Astra stochasticity or multiple acceptable plans can also generate label disagreement; exact imitation is stricter than independent task-effect equivalence. The prompt may intentionally omit state that Astra sees in the image. A richer deterministic typed state may resolve the ambiguity without a learned backend.

**U:** one held-out retained allocation, five eligible rows, one domain/fixture family. No population reliability or learned-policy efficacy claim. No new latency benchmark was run, so hardware/clock uncertainty and calibrated `u_c`/coverage factor `k` are not applicable here.

## Smallest next representation discriminator

Do **not** train a learner on the current signature.

The v31 collision exposes a cheaper candidate than adding a visual encoder. Iteration 1 follows no admitted prior plan, whereas iteration 2 follows an admitted `retreat_fire(short)` whose effect receipt is `visible_change`. The current text carries only `Previous no-visible-effect actions`, so successful/visible-change effect history is discarded.

The next one-variable representation candidate is therefore:

```text
last_effect_receipt = NONE
or
last_effect_receipt = {action, extent, result}
```

This is caller-available retained evidence, not authority and not a future oracle. First test whether adding exactly this feature family removes the known v30/v31 collisions while preserving UNKNOWN/YIELD and without using image semantics. Only after a representation is functionally consistent should RULE → LINEAR → TREE → TINY POLICY be compared on fresh labels.

## Integrity / retention

The runner and independent auditor were committed and read back before the held-out prompt/action inspection. All eight materialized prompt byte strings were independently Git-object hashed and matched their retained Git blobs before the sole formal invocation. `SOURCE_ROWS.json`, `RESULT.json`, `AUDIT.json`, plan, runner and auditor are retained additively under this research namespace. Existing MAP01 and System-1 negative evidence is unchanged.
