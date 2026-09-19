# Evidence-bound semantic differences — #2004 successor

Finite standard-library audit of typed differences between two observations.
Facts are emitted only when session, surface, observation identity, and epoch
are consistent. Stale, replaced, malformed, or ambiguous pairs fail closed.

This is model-facing evidence only: it grants no action authority and makes no
claim about GUI correctness, model usability, latency, or cross-domain transfer.

Run:

```text
python research/analysis/semantic_difference_evidence_successor_2004_v1/audit.py
```
