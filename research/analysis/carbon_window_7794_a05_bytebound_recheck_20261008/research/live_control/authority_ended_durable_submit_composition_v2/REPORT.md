# Durable authority token × durable submit composition v1

Status: **RETAIN_COMPOSITION_BOUNDARY / HOLD_ATOMIC_EXACTLY_ONCE**.

Base: `d21482d1a3cc16b54447d14d0a2d93aa70409162`. Tracks Issue #156. This is an additive offline mechanism-isolation experiment: no model, GUI, OS input, network, runtime mutation, or production promotion.

## Why this experiment exists

The retained `authority_ended_restart_durability_v1` result closes caller-process replay for a runtime-owned authority-end token by durably storing `pending | consumed`. It explicitly leaves one gap: a crash after durable `consumed` but before OS submit can lose liveness. The repository already has a separate `durable_submit` family that persists `may_have_been_sent` before transport and recovers unresolved delivery read-only. The question here is whether simply composing those two existing mechanisms closes the remaining gap.

It does not make the two journals atomic. It does, however, sharply localize the uncertainty boundary.

## Frozen executable sources

The runner aborts unless the following Git blob identities match the base repository:

- `authority_ended_restart_durability_v1/durable_token_state_v2.py`: `e48f4e2c1949ffd494a7e4e61510e9d3148aa646`;
- `authority_ended_restart_durability_v1/authority_ended_bridge_v1.py`: `9fcfdce5229cb58b3d1a17aacbcef0cb44bd10f1`;
- `durable_submit_v1.py`: `aaee9d460bcf114dbe1603056c79e6ecc65403e2`;
- `received_continuation_v1.py`: `b27d922799cfcfc66ad092c8edb8b7134e1889e5`;
- `unix_json_deadline.py`: `267b5ccce24ca43b8a6e9b36219d50342888aa27`;
- retained receipt fixture: `4070fd206c859357125a2cb327affa5aec6de8b8`.

The executable uses `durable_submit_v1` because it is the minimal submit-only form of the existing contract. Current `durable_submit_v6.py` at the base (`953e1f1ef5816f7364e5d2c1de89ce0e69193d72`) retains the same relevant ordering for submit: construct `pending` → persist journal → invoke transport. Its additional clock/effect-checkpoint paths are irrelevant to this crash-cut question.

Frozen preregistration SHA-256: `132620fa8c54f6560cc6fae2aceec29f142be8da653caeca6ffe7f14c969b007`.

Frozen runner SHA-256: `433ebe483cf7750ea441a0ece323d721b82aa3961af86952583b8bf811005212`.

## First-outcome matrix

One frozen matrix, zero tuning or rerun after outcome. Six of six gates passed.

| Cut/control | Retained outcome |
|---|---|
| Pending authority token, no submit | `TOKEN_PENDING_NO_SUBMIT` |
| Crash immediately after durable token consume, before `durable_submit.run` | `CONSUMED_WITHOUT_SUBMIT_RECORD` |
| Crash inside injected transport after durable-submit pre-transport persist | `PENDING_OR_UNKNOWN_DELIVERY`; `write_state=may_have_been_sent` |
| Restart attempts a new command while that submit is pending | rejected as `unresolved command; read only`; transport not called |
| Restart performs one command-free timeout read | same pending request identity survives; no command in request |
| Reverse order: call durable submit before token consume | transport callback is reached while token status is still `pending` |

The crash exits are deterministic harness cuts: 81 between the two journals, 82 after durable-submit persistence at transport entry, and 83 for the reverse-order control. They are not runtime error codes.

## Interpretation

There are three distinct states, and collapsing them would be a correctness error:

1. **Token pending / no submit record.** Replan authority can still be recovered under the retained durable-token contract.
2. **Token consumed / no submit record.** This is the inter-journal gap. The old token is no longer recoverable, but there is no durable request/action identity to reconcile. Existing `durable_submit` cannot infer delivery because it was never entered. A safe supervisor must fail closed and reacquire fresh authority/evidence; it must not pretend this is exactly-once continuation.
3. **Token consumed / durable submit pending.** Delivery is explicitly uncertain. The existing durable-submit contract already prevents blind replay and permits only read-only reconciliation until the exact request resolves.

Reversing the calls is not a fix: `durable_submit.run` persists and immediately enters transport, so submit-before-consume can reach transport while the authority token remains pending. There is no prepare-only handoff in this existing call path.

Therefore the repository already has the right mechanism for **post-submit-journal uncertainty containment**, but not an atomic bridge between durable authority consumption and durable request preparation.

## H / T / D / C / U

**H.** Naive `token.consume() -> durable_submit.run()` leaves an inter-journal crash cut; after durable-submit persistence, its existing journal preserves explicit uncertainty and blocks blind replay.

**T.** Separate Python subprocesses over byte-identified retained sources; injected transport only. Minimum crash cuts plus reverse-order control. One first-outcome matrix.

**D.** **RETAIN_COMPOSITION_BOUNDARY / HOLD_ATOMIC_EXACTLY_ONCE.** All six frozen gates pass. Only the post-submit-journal region is covered by durable delivery uncertainty.

**C.** A prepare-only boundary that durably reserves the request identity before consuming the authority token, or an effect/action owner that makes request identity idempotent, could close the inter-journal ambiguity. Neither is introduced here.

**U.** CPython 3.13.5, Linux 6.18.44 x86_64, 5 visible CPUs, local container filesystem, single writer. No power-loss, runtime crash, hostile-state, network, GUI, model, or real input claim.

## Next smallest discriminator

Before adding a new prepare phase, search and test whether the runtime/action owner already has a request/action identity replay rule strong enough to make a repeated identified submission return the prior admission/terminal outcome without a second physical admission. If such owner-side idempotency exists, compose with it. If not, the honest boundary is fail-closed reacquisition after `CONSUMED_WITHOUT_SUBMIT_RECORD`; adding a client-side transaction protocol should then be a separate, explicitly justified research generation.
