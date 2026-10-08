# Successor #1979 audit

## Frozen result

- 4 typed events; all 24 permutations exhaustively enumerated.
- `RECENCY_ONLY`: exact 0/24 against the causal/relevance oracle.
- `CAUSAL_THEN_RECENCY`: exact 24/24.
- Raw event identities were retained in every ranking.
- Manifest SHA-256: `80068606ab99a3344e5ecd5948f049a526001eb5332aa40ceda72f038c6eb225`.
- Python: 3.14.5.
- Independent second implementation: PASS, 24 streams, causal exact 24/24, recency counterexample present.

## Scope

`PASS_CAUSAL_RELEVANCE_ORACLE_SCOPED`. This is a finite synthetic ranking result only. It does not establish model attention usability, automatic causal labeling, GUI correctness, token/latency savings, or transfer.

## Stop disposition

STOP after the frozen exhaustive result and independent audit. No model, GUI, network, or runtime calls were made.
