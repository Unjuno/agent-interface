# #1726 O3 relevance-completeness provenance — retained formal result

Task: `OBSERVATION-GATING-O3-RELEVANCE-COMPLETENESS-20260918-001`

Decision: **`PASS_O3_RELEVANCE_COMPLETENESS_SCOPED`**.

## Question

#1583 binds O3 relevance to a current relevance generation, and #1645 adds intent/currentness binding. Those mechanisms answer whether a relevance declaration is current. They do not prove that the current declaration contains every semantically relevant tile.

This experiment isolates completeness.

## Analytical witness

Hold all gate-visible fields fixed: scope, current relevance generation, current intent epoch, declared relevance A, changed tile x outside A, and noncritical status.

Two worlds can be observationally identical to the gate:

- W0: x is truly irrelevant -> suppression is allowed.
- W1: x is a current semantic dependency omitted from A -> forwarding is required.

A deterministic gate using only the current declaration cannot distinguish the worlds. Therefore nontrivial suppression outside A requires a trusted completeness guarantee somewhere in the contract.

## Policies

- `ASSUME_COMPLETE`: every current relevance declaration is treated as complete.
- `COMPLETE_ONLY`: suppression is allowed only for current `PROVEN_COMPLETE` declarations. `PARTIAL` and `UNKNOWN` fail open to full-current evidence.

A forged PROVEN_COMPLETE control intentionally shows that the completeness claim itself must come from trusted provenance or a by-construction semantic contract.

## Formal

Exactly one exhaustive invocation; reruns/replacements/tuning `0/0/0`.

State space:
- six tiles;
- all 64 true semantic relevance sets;
- all 64 declared relevance sets;
- each of six changed tiles;
- critical status either none or the changed tile.

Total: **49,152 rows**.

| Metric | Result |
|---|---:|
| ASSUME_COMPLETE false suppressions | **6,144** |
| ASSUME_COMPLETE safe suppressions | 6,144 |
| truthful COMPLETE_ONLY false suppressions | **0** |
| truthful COMPLETE_ONLY safe suppressions | **192** |
| PARTIAL suppressions | **0** |
| UNKNOWN suppressions | **0** |
| stale-currentness suppressions | **0** |
| forged-complete false suppressions | **6,144** |

Independent audit re-derived the exact counts in closed form:

- total rows = `2^6 × 2^6 × 6 × 2 = 49,152`;
- omission escapes = `6 × 2^5 × 2^5 = 6,144`;
- truthful complete safe suppressions = `6 × 2^5 = 192`.

Candidate source and audit remained source-hash exact after formal. Corruption controls: **7/7 reject**.

## Excluded preflight

Before GitHub allocation, a local allocation-selection preflight was performed. Its v1 stopped before result because a Python `frozenset` was written directly to JSON; scientific rows0. A representation-only v2 and an independent closed-form checker indicated that a successor was worth opening.

Those artifacts are explicitly non-poolable and are not part of this formal result.

## Interpretation

Currentness and completeness are separate authority questions:

- generation / intent epoch: is this declaration current?
- completeness provenance: is everything outside this declaration safe to omit?

A fresh but incomplete relevance map can still hide a current semantically important change.

The result does not require a literal `coverage` field. An interaction ISA or deterministic compiler can guarantee completeness by construction. But if relevance is heuristic or model-produced, a claimed completeness flag is only as strong as its provenance.

## Integrity

- formal result SHA-256: `16b47adf51c54f92b6bc3af8fa94216e08f0adfb8412234eee643b5e918ab59f`;
- audit SHA-256: `4f14cc9291ec2af2d3aaaddb32d84e409c23eb593e88223cf5cc4a7497d2e09c`;
- deterministic ledger SHA-256: `40e48780b670ed147f3de34f36ef6d129c232411ce1ccee54863fcdb683396e1`.

## Boundary

Synthetic exact semantics only. No real relevance-inference accuracy, GUI prevalence, model task quality, image-token reduction, latency, or production ABI claim. O1/O2/O3 live-transfer/O4 remain independently owned.
