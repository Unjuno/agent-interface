# One-use confirmation transition consumption

Task: `COORD-ONE-USE-TRANSITION-CONSUMPTION-20260916-018`

Decision: **`PASS_ONE_USE_CONFIRMATION_TRANSITION_SCOPED`**

## Question

Does binding confirmation freshness into the canonical CAS record also make that confirmation one-use, or must successful generation transition explicitly consume the confirmation identity?

## First outcome

| Case | First transition | Same identity second transition | Final |
|---|---|---|---|
| reusable baseline | g1 -> g2 | **authorized and committed** g2 -> g3 | g3, confirmation rev1 reused twice |
| one-use candidate | g1 -> g2 + consume rev1 | `HOLD_CONFIRMATION_CONSUMED`, write 0 | g2, rev1 consumed for g2 |
| fresh confirmation control | g1 -> g2 + consume rev1; install same-content rev2 | rev2 authorizes g2 -> g3 once | g3, rev2 consumed for g3 |

Baseline commits: `0319f35aae2d4649ef71fc7f4bd7b7c88f757456`, `38e44b964df6ca7ce6441db0de29313dcf59e6c5`.

Candidate first transition: `c7c7b41cf315cb1805bdf8efedb33855b399d885`. The second use was refused by frozen policy before any update call.

Fresh-control commits: first consume `2c2774491b4503368b5912b8a621516faaac243b`, fresh rev2 install `de22ab342e0f7f5a16105528afcb258f472fc044`, rev2 transition `274989740b2ea65aaf569f6d1ff499b4eeffd998`.

## Interpretation

Confirmation freshness and confirmation consumption are distinct invariants. A canonical record may prove that `(content_id, revision)` is current while still allowing the exact same identity to authorize multiple later generation changes. In this fixture, atomically setting `confirmation_consumed=true` in the successful generation transition closes that reuse path. A new confirmation revision can restore liveness without changing semantic content.

This suggests the transition CAS identity must encode not only what confirmation is current, but also whether that specific confirmation instance has already been spent for an authority-changing transition.

## Boundary

Sequential GitHub-backed fixture only. The confirmation producer and membership author are trusted fixture inputs. This does not establish authenticated provenance, simultaneous-request linearizability, distributed consensus, crash/power-loss behavior, quorum availability, external-effect exactly-once semantics, or a production ABI.

`verify.py` is retained deterministic checking code and was not independently executed from a checkout in this session.

## Next single question

Keep one-use confirmation consumption fixed and test acknowledgment loss after the successful consuming transition. If the transition commit succeeded but its response is unavailable to the caller, content-bound readback should recognize that the confirmation was already consumed and must not mint/install a fresh confirmation revision merely to repeat the same intended transition. Test exact-self readback versus changed generation/confirmation state; no retry loop or timeout inference in that rung.
