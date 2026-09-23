# All-receiver barrier confirmation before generation advance

Task: `COORD-BARRIER-FANOUT-ALL-CONFIRMED-20260916-013`

Decision: **`PASS_ALL_RECEIVER_BARRIER_CONFIRM_SCOPED`**

## Question

Hold the single-receiver content-bound barrier classifier from #449 fixed and change only fanout cardinality to two receivers. Coordination may advance from generation 1 to 2 only when **both** receivers are byte-exact `BARRIER_CONFIRMED`.

## First outcome

| Case | Receiver A | Receiver B | Aggregate | Coordination final |
|---|---|---|---|---|
| `all_exact` | confirmed | confirmed | `ALL_CONFIRMED` | generation 2 |
| `one_changed` | confirmed | conflict (`ACTIVE/g1/revision2`) | `HOLD_CONFLICT` | generation 1 |
| `one_unavailable` | confirmed | unknown (`UNAVAILABLE` classifier fixture) | `HOLD_UNKNOWN` | generation 1 |

All six initial receiver barrier updates succeeded exactly once. The changed case then performed its one frozen intervening update. Classifier reads were five real GitHub GETs plus one frozen unavailable observation. Receiver recovery PUT count was zero. Only the all-exact case performed a coordination update.

The later evaluator-only read in `one_unavailable` showed receiver B had in fact committed the expected BLOCKED bytes. That later knowledge did not retroactively change the scored `HOLD_UNKNOWN` decision.

## Interpretation

In this two-receiver fixture, single-receiver confirmation is not sufficient authority for a global generation advance. Requiring exact confirmation from every frozen receiver prevents coordination generation 1 from becoming stale while any receiver is changed or unobserved.

The `one_changed` case is the sharper discriminator: receiver A is fully confirmed, while receiver B has returned to `ACTIVE/g1`. The global rule holds coordination at generation 1 rather than advancing and thereby turning B's still-admitted generation-1 work into stale authority.

## Counts

- initial barrier updates: 6/6 successful
- intervening receiver updates: 1
- classifier real GETs: 5
- classifier unavailable fixtures: 1
- receiver classifications: 4 confirmed / 1 conflict / 1 unknown
- receiver recovery PUTs: 0
- coordination updates: 1
- global outcomes: 1 `ALL_CONFIRMED`, 1 `HOLD_CONFLICT`, 1 `HOLD_UNKNOWN`
- timeout inference: none
- quorum/majority optimization: none

## Evidence boundary

This is sequential GitHub-backed fixture evidence. It does not establish simultaneous broadcast, transport fault handling, distributed consensus, quorum availability, process crash behavior, atomic fanout, or an external task-effect guarantee. No effect request was executed in this rung; the safety claim is specifically that coordination does not create stale generation-1 authority while a receiver remains unconfirmed.

The receiver set `{A, B}` is fixture-provided and immutable during each case. Therefore this result does **not** establish which receiver membership snapshot must be fenced if receivers join, leave, restart under a new identity, or are replaced during handoff.

`verify.py` is retained deterministic checking code; no independent execution is claimed.

## Next single question

Keep all-confirmed aggregation and content-bound per-receiver confirmation fixed. Vary only **receiver membership identity**: freeze a membership epoch/set before barrier installation, then introduce a receiver-set change during handoff. Test whether coordination advance is allowed only when confirmations are bound to the same frozen membership epoch, rather than accidentally omitting a newly authoritative receiver or waiting on a retired identity. Do not add quorum thresholds or timeout-based membership eviction in that first membership rung.
