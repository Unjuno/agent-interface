# Successor #1979 result

## H/T/D/C/U

- **H**: causal relevance should dominate temporal decay, while recency resolves equal-relevance history.
- **T**: exhaustively enumerate all length-4 streams over current-causal, older-causal, older-irrelevant, and unexpected events. Compare RECENCY_ONLY and CAUSAL_THEN_RECENCY against the explicit oracle.
- **D**: 256 streams, full rankings, counterexample traces, manifest SHA-256, and formal/audit counters.
- **C**: CAUSAL_THEN_RECENCY must match the oracle on every stream; RECENCY_ONLY must expose causal counterexamples; raw events are never discarded.
- **Competing explanations**: this oracle encodes the causal labels as frozen truth; no automatic causal labeling or real temporal workload is tested.
- **U**: model attention usability, cue overload, real latency/tokens, GUI correctness, and cross-domain transfer.

## Formal result

```text
streams                  256
CAUSAL_THEN_RECENCY      exact 256/256
RECENCY_ONLY             exact 80/256
recency counterexamples  176
formal                    1
audit                     1
reruns                    0
tuning                    0
manifest SHA-256          7e0759330a1df24a7170176d3ea687692a73716e4bc03000607455423a2a6780
```

First counterexample: `current_causal, current_causal, older_irrelevant, current_causal`. Recency places the irrelevant event ahead of the later causal event; causal-first ranking returns the oracle order.

**Scoped outcome: PASS_CAUSAL_RELEVANCE_DOMINATES_RECENCY_SCOPED.**

This is an exhaustive synthetic policy result only. It does not establish automatic causal labeling, model quality, latency, token savings, GUI behavior, or transfer.

