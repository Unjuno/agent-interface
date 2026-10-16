# Decision-useful multiple descriptions under loss

- **Status:** Unverified transfer proposal; novelty boundary narrowed by prior-art update.
- **Source:** [Issue #8875](https://github.com/Unjuno/agent-interface/issues/8875), successor to #5350, #5459, and #8865.
- **Idea:** Under lossy delivery, compare semantic descriptions by whether each received subset yields a conservative set of still-plausible task decisions, never excluding the frozen oracle-optimal choice, while remaining non-authoritative.
- **Prior art:** Semantic multiple-description coding is already studied in external 2025–2026 work. The proposal must not claim novelty for semantic MDC, packet-loss redundancy, or degraded reconstruction from any subset. Its narrower discriminator is the conservative decision-set invariant, distinct from source/image reconstruction quality and exact-window FEC recovery.
- **Boundary:** No transport implementation or current GUI-feedback-loss finding is reported. A future finite pass would not establish semantic correctness, freshness, authority, or safe GUI action.
