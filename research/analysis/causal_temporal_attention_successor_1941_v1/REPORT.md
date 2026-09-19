# Issue #1979 successor — causal relevance versus temporal decay

## H/T/D/C/U

- **H:** A typed causal-relevance boost prevents an older causally relevant observation from being outranked by newer irrelevant observations, while recency resolves equal-relevance history.
- **T:** Exhaustively enumerate all streams of lengths 1–5 over current-causal, older-causal, older-irrelevant, and unexpected observations. Compare RECENCY_ONLY and CAUSAL_THEN_RECENCY to an explicit oracle.
- **D:** `experiment.py`, 1,364 streams, raw stream SHA-256 values, exact ranking/reconstruction assertions, and this report.
- **C:** CAUSAL_THEN_RECENCY must match the oracle on every stream; RECENCY_ONLY must have a causal counterexample; raw evidence must remain recoverable.
- **U:** Model attention usability, automatic causal labeling, cue overload, real latency/tokens, GUI correctness, and transfer remain unknown.
- **STOP:** One finite exhaustive result; no model, GUI, network, runtime, or user data.

## Result

Command: `python experiment.py`

- Enumerated **1,364** streams.
- CAUSAL_THEN_RECENCY matched the oracle on **1,364/1,364** streams.
- RECENCY_ONLY produced **1,044** counterexamples.
- First counterexample: `(current_causal, older_irrelevant)`; recency selects the irrelevant observation first, while the causal policy matches the oracle.
- Reconstruction matched the original stream for every policy/oracle comparison.

**Decision: PASS_CAUSAL_RELEVANCE_RANKING_SCOPED.**

This is a finite synthetic ranking result only. It does not establish model usability, automatic causal labeling, token/latency savings, GUI correctness, or cross-domain transfer.
