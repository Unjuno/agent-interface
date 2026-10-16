# #2802 Allocation 05 — actual transport drop and hidden-state provenance

Disposition: **PASS_APP_TRANSPORT_DROP_BOUNDARY_SCOPED**.

## Frozen question

Can a temporal consumer distinguish (a) an application event that never happened, (b) an event that happened but was dropped in transport, (c) an unreported predicate/state transition while event sequence remains contiguous, and (d) mere delivery delay?

## Formal result

One prospectively frozen formal invocation completed all 18 fresh producer/relay process pairs. Formal reruns/replacements/post-freeze tuning: 0/0/0.

| Candidate result | Count |
|---|---:|
| SATISFIED | 6 |
| EXPIRED | 3 |
| UNKNOWN_GAP | 3 |
| UNKNOWN_HIDDEN_CHANGE | 3 |
| UNKNOWN_DUPLICATE | 3 |

All 18 producer exits and all 18 relay exits were 0. COMPLETE_AB and DELAYED_DELIVERY_B were SATISFIED in all three repetitions each; the 50 ms relay delay did not rewrite the producer's source-time B timestamp. LATE_B expired in all three repetitions.

In DROP_B, the producer truth ledger contains B but the relay omits it; the next forwarded H has a source-event sequence gap, so the candidate returns UNKNOWN_GAP 3/3. In HIDDEN_STATE_CHANGE, event sequence stays contiguous while cooperative application-state revision jumps from1 to3 after two scoring-only hidden changes; candidate returns UNKNOWN_HIDDEN_CHANGE 3/3. In DUPLICATE_A, the relay forwards the same A record twice and candidate returns UNKNOWN_DUPLICATE 3/3.

The deliberately unsafe timestamp-only comparator ignores source-event sequence and state revision. It makes **9 unsupported terminal claims in 9/9 provenance-negative cases**: EXPIRED for all DROP_B/HIDDEN_STATE_CHANGE cases and SATISFIED for all DUPLICATE_A cases. This is a comparator result, not an allegation that current production code implements that policy.

## Audit / integrity

Independent raw-only audit: errors=[]. Eight copied-evidence corruption controls all reject. Five policy unit methods pass. Exact identities:

- formal RAW SHA-256 `324921c22318b7a41fec21cf606d53e130b7a3f31884b9d0b5fddd3101f37892`
- formal SUMMARY SHA-256 `868f9343200c96ba886d62b193885235f613259a086538651cb11eb06411a304`
- result SHA-256 `98897a6b4d49a880cf9196c67fdb5ef117d242ab2cbe7a71abcca409b572c1fb`
- audit stdout SHA-256 `1847122b5d427aa53c59bb5d353b7704fe29f26d8506be2b6a62fbe5ac7b3dfe`

Preformal GitHub freeze HEAD `1e50454b395b7871d3cd725e23b72a9b346304ac`; source-bundle Git blob `f2a19ccd4768da2b4700cf40b8ff86ece8b27a2c`; gzip SHA-256 `8897b7518f1efe0f54adac0f42c0fc25cea8af8cc8a684baf7d166a6907f22c5`. All six scientific source SHA-256 values match the preformal FREEZE.

Construction is separate. Construction-01 retained one auditor-control deficiency (7/8) before formal0. Only the construction denominator check in audit.py changed. Construction-02 then passed6/6, audit errors=[],8/8 controls; the final source hashes were frozen remotely before formal.

## H / T / D / C / U

**H:** Source-event continuity distinguishes transport loss from source absence; a separate state revision distinguishes hidden predicate changes even when event sequence is contiguous. Arrival delay alone must not change source-time success; duplicate delivery is not a second authoritative observation.

**T:** Six scenarios x three cyclic repetitions over actual producer→relay→consumer OS pipes. Source bound20ms; delayed-delivery relay sleeps50ms. Producer truth/state ledger is scoring-only. Candidate sees only forwarded records.

**D:** All frozen gates pass:18/18 rows,36/36 zero exits, exact candidate totals,9/9 unsafe comparator unsupported terminal claims, delayed source-time success3/3, audit errors=[],8/8 corruption controls.

**C:** Trusted single producer, one relay, one Linux host/CLOCK_MONOTONIC. Sequence/revision fields are cooperative fixture contracts, not authentication. The hidden revision is explicit instrumentation and does not prove arbitrary applications can expose equivalent evidence.

**U:** No reconnect/wrap, simultaneous obligations, hostile producer, cross-host clock comparison, GUI/model/task utility, task input/authority, natural reliability estimate, token/latency benefit, production runtime/default or cross-platform claim. Same-author separate implementation/process audit is not external human review.

## Integration decision

For #2802's temporal transfer, a missing received event cannot by itself be interpreted as a source-time negative outcome. A transport completeness signal (such as contiguous source sequence) and, where predicates can change without events, a state-version/completeness signal are required before terminal temporal claims. Delivery delay is separate from source-event time.

This closes only this transport/state-provenance rung. Broad #2802 remains open for simultaneous obligations/reconnect/wrap and broader live application semantics.
