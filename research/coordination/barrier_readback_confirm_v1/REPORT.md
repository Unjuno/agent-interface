# Content-bound barrier confirmation after withheld write response

Task: `COORD-BARRIER-READBACK-CONFIRM-20260916-012`  
Issue: #449  
Publication BASE: `c00de06ff3b94655dec1d346a360bcde61d37476`  
Freeze commit: `8dff4017a6bddde15e71b8f3051d8a49edd4ef21`

## Decision

**`PASS_CONTENT_BOUND_BARRIER_READBACK_SCOPED`**

The retained first outcomes support one narrow rule for the receiver-first barrier protocol from #433 / PR #439:

> When the barrier-install update response is not available to the recovery classifier, coordination may advance only after a fresh readback is byte-identical to the exact expected BLOCKED receiver state. A BLOCKED label alone is not sufficient, and unavailable evidence remains UNKNOWN.

## Frozen cases and first outcomes

| Case | Initial barrier update | Recovery evidence | Classification | Receiver recovery PUT | Coordination result |
|---|---|---|---|---:|---|
| `exact_barrier_readback` | success, commit `efbf9d220494cce720195c43bbcb2c0c77420854` | one real GET, exact expected bytes | `BARRIER_CONFIRMED` | 0 | one g1->g2 commit `e601bae44a822896e92f79a47cbb902b67be6423` |
| `changed_barrier_readback` | success, commit `62f73fb1525b0e7b3f24cf263e3b254530874721` | prescribed intervening commit `4ecf0f4790efdbbbd9bccb708d9594eed4e1ed88`; one GET returns different BLOCKED bytes | `BARRIER_CONFLICT` | 0 | remains g1 |
| `unavailable_barrier_observation` | success, commit `657cd96c2280764672e4f9b4a27818cae3486809` | frozen fixture `UNAVAILABLE` | `BARRIER_UNKNOWN` | 0 | remains g1 |

Totals:

- initial barrier updates: 3/3 succeeded once;
- prescribed intervening receiver updates: 1;
- classifier real GETs: 2;
- fixture unavailable observations: 1;
- receiver recovery PUTs: **0**;
- coordination updates: **1**, exact-confirmation case only;
- second classifier readbacks: 0;
- mode-only confirmations: 0;
- timeout inference: none.

## Key controls

### Exact-content confirmation

The exact-case receiver readback is byte-identical to frozen `payload_barrier_exact.json`. Only this case grants `advance_coordination=true`.

### BLOCKED mode is not enough

The changed case remains semantically `mode: BLOCKED`, `accepted_generation: 1`, and has no effects, but its frozen intervening update changes the record from revision 1 to revision 2. Because the bytes differ from the expected barrier record, the classifier returns `BARRIER_CONFLICT`; coordination remains generation 1.

This is the primary negative control against a mode-only recovery rule.

### Later evaluator knowledge does not rewrite the UNKNOWN decision

In the unavailable case, the initial barrier update actually committed the expected BLOCKED bytes, but the classifier received only frozen `UNAVAILABLE`. It therefore returned `BARRIER_UNKNOWN` and coordination remained generation 1. A later evaluator-only GET confirmed the committed bytes for retention/integrity; that later information was not fed back into the scored classifier decision.

## Evidence boundary

This experiment does **not** inject a real transport fault. The successful update response is deliberately withheld from classifier input, and `UNAVAILABLE` is an authored fixture observation. The result establishes bounded fail-closed decision composition under those evidence conditions, not availability or packet-loss behavior of GitHub.

The changed case is a prescribed sequential intervening mutation, not a simultaneous-request linearizability test.

The GitHub contents files are fixture state, not a production receiver service. No GUI/input effect, external service, crash/power loss, clock/TTL, or exactly-once execution claim is made.

## Retained artifacts

- `policy.py` — frozen exact-content classifier;
- `plan.json` — finite schedule and budgets;
- `freeze.json` — pre-measurement Git blob identities;
- three receiver and three coordination state files;
- frozen expected/intervening/update payloads;
- `result.json` — measured first outcomes;
- `verify.py` — deterministic offline checker, retained but not claimed independently executed;
- this report.

## Next single question

Keep content-bound confirmation and the receiver-first barrier fixed, and vary only **receiver fanout**. With two independent effect receivers, can coordination advance only after both receivers have exact-confirmed BLOCKED state, while one changed or unavailable receiver forces a global HOLD and prevents a stale effect through the unconfirmed receiver?

This next rung should not introduce quorum thresholds, timeout reclaim, or availability optimization. First establish the all-confirmed safety baseline before considering weaker fanout rules.
