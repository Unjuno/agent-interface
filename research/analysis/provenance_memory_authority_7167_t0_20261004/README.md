# Issue #7167 T0 — provenance-bound object memory

This deterministic, no-network test asks whether source authority survives
memory storage, summary/consolidation, and retrieval. It uses exact synthetic
records only; it is not a model prompt-injection test, live vulnerability, or
security guarantee. The finite contract refuses to emit application content,
model hypotheses, derived summaries, or missing-source records as
user-authorized instructions while retaining their descriptive text and
provenance.

See `FREEZE.json` for the frozen hypothesis, corpus, transformations, decision
gate, and one-shot invocation budget. Pre-freeze construction checks (if any)
are documented separately from `formal_01/`.
