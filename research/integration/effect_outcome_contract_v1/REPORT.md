# Typed effect outcome reducer construction v1

Task `EFFECT-OUTCOME-CONTRACT-CONSTRUCTION-20260916-001`, Issue #464.
Construction base: `33c8c538fc763fee2d05f8e5bc915888352b82b1`.

Decision: **`PASS_CONSTRUCTION_CANDIDATE`**.

## Purpose

This additive construction turns two retained result-contract findings into one small, reviewable candidate reducer:

1. a pre-effect refusal is not the same event as a post-effect contradiction;
2. a verified compensation can restore current state without erasing the historical wrong effect.

This is not a production ABI or shared-runtime promotion. The candidate intentionally supports only the evidence-bounded states listed below and fails closed outside them.

## Candidate contract

Supported reductions:

| Evidence | Outcome |
|---|---|
| stageable publication commits intended state | `PUBLISHED_VERIFIED` |
| terminal refusal occurs before any authoritative effect and state is unchanged | `REJECTED_PRE_EFFECT` |
| direct primary effect commits intended state | `EFFECT_VERIFIED` |
| direct primary effect commits a wrong state with no compensation | `EFFECT_CONTRADICTED_UNCOMPENSATED` |
| direct wrong effect is followed by one compensation restoring the declared initial invariant | `EFFECT_CONTRADICTED_COMPENSATED` |

The returned `Outcome` separately records `effect_occurred`, intended-effect verification, contradiction, compensation attempt/verification, current state, and the ordered immutable history. In particular, compensated contradiction keeps `effect_occurred=True` and the original wrong-effect event.

Fail-closed cases include effect history attached to a pre-effect refusal, compensation without a preceding primary effect, non-monotone sequence numbers, final-state/history mismatch, duplicate primary effects, failed/partial compensation, a wrong stageable publication, and an unsupported compensation after a verified intended effect.

## Test receipt

Exact local source bytes were copied into a fresh temporary directory before the second run.

- `python -m py_compile outcome.py test_outcome.py`: PASS
- `python -m unittest -v`: **18/18 PASS**
- test reruns after source change: 0 (there was no source change between first and clean-copy runs)

SHA-256:

- `outcome.py`: `db0a9dfe31aa406dc0ceea2c13552be974226281eb0a33413bffe104e8b7e548`
- `test_outcome.py`: `3c87f7b793214121d272a321734d029c6960cd9ee21209bb4cb2fcf63fbb5f18`

These hashes identify the bytes intended for GitHub publication. Publication readback is checked separately by Git blob identity.

## H / T / D / C / U

**H.** Explicit phase plus ordered effect history is sufficient to preserve the retained pre-effect/post-effect and compensated-history distinctions for this bounded contract.

**T.** Pure standard-library reducer plus deterministic unit tests; no live effect, model, GUI, network, game, benchmark, or user data.

**D.** `PASS_CONSTRUCTION_CANDIDATE`: all five supported reductions classify as intended, compensated contradiction preserves effect occurrence/history, and malformed or unsupported histories reject in the frozen test matrix.

**C.** The retained compensation evidence covers one authored scalar invariant. A compensation might restore that primary value while damaging a collateral property; this candidate deliberately refuses to infer broader safety from restoration of one value.

**U.** No evidence here for concurrency, crash/power-loss durability, distributed effects, partial compensation, collateral-effect verification, natural failure rate, performance, or production API stability.

## Next smallest question

Before shared-runtime integration, test the upstream unresolved compensation boundary: restore the primary target but mutate a preserved collateral property. The reducer should not call that fully compensated unless both the declared primary invariant and required collateral invariants are independently verified.
