# Issue #7367 — use-graph completeness boundary A01

**Disposition: `COMPLETENESS_CONTRACT_GAP_DEMONSTRATED`.** This is a deterministic host-side contract probe over the frozen A01 candidate. It is not a method failure: the candidate is correct when the declared graph is complete. It shows that the `graph_complete` assertion is not itself evidence of completeness, so A01's separate completeness-contract gate remains open.

## H / T / D / C / U

**H.** If a caller supplies a graph that omits a real future consumer while still asserting `graph_complete=true` and `dynamic_consumers_possible=false`, the A01 candidate can evict the consumer's required evidence. If the caller truthfully reports uncertainty, the candidate retains all records as `UNKNOWN_KEEP`.

**T.** Run the unchanged A01 `analyze` function over the exact main-pinned workload and freeze. Keep its declared graph fixed while an independent counterfactual workflow oracle adds a hidden future consumer of `completed-note.terminal_receipt`. Then flip only the scope to unknown and confirm fail-closed retention.

**D.** `COMPLETENESS_CONTRACT_GAP_DEMONSTRATED` if the declared-graph candidate evicts `completed-note` while the counterfactual oracle requires it, and the unknown-scope control returns `UNKNOWN_KEEP` with no eviction. Otherwise `NOT_REPRODUCED`.

**C.** This is not a defect when the upstream workflow producer can prove an exhaustive consumer graph and prevent unmodeled dynamic reads. A01 already handles an honestly declared dynamic consumer by abstaining.

**U.** The omitted consumer is an explicit counterfactual, not a real Agent Interface workflow. No model, runtime, persistent-store deletion, GUI, live action, or task outcome was exercised. The probe establishes the exact limit of a self-declared completeness bit only.

## Result

The candidate returned `PROVEN_DEAD_EVICTION` and evicted `completed-note`; the counterfactual consumer requires its `terminal_receipt`. The honest unknown-scope control returned `UNKNOWN_KEEP` and evicted nothing. The completeness assertion is therefore an external precondition. A model rung remains HOLD until a separate contract binds the declared graph to an exhaustive workflow/consumer source and rejects unmodeled dynamic reads before pruning.

## Reproduction

Run `python run_a01.py --out RAW.json`, then `python audit_a01.py RAW.json --out AUDIT.json`. The candidate imports the frozen A01 `run_a01.py` without modifying or rerunning its original allocation. `SHA256SUMS.txt` pins this package, the A01 workload/freeze/source, and resulting outputs.
