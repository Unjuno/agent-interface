# Behavioral equivalence across benchmark variants — #8920

- **Status:** Unverified proposal; no allocation or result is recorded.
- **Source:** Open [Issue #8920](https://github.com/Unjuno/agent-interface/issues/8920).
- **Idea:** Compare endpoint-only task-contract matching with a finite labeled-transition equivalence audit. Freeze the abstract action vocabulary, propositions, observation/effect labels, and cosmetic-label mapping before scoring variants. Distinguish equivalent cosmetic variants from changes to enabled actions, forbidden intermediate states, preconditions, or recovery edges; return `UNKNOWN` when the transition model is incomplete.
- **Overlap:** #12 defines task contracts and freshness classes; #8890 studies transfer of a reusable macro across functional changes; #5784 tests reset fidelity across histories. #8920 instead qualifies the authored task-variant models. Its equivalence certificate would be relative to those models and assumptions.
- **Boundary:** No existing benchmark cohort is shown invalid. Equivalence does not establish equal difficulty, visual/perceptual equivalence, timing or token-cost equivalence, policy transfer, or statistical exchangeability. No result permits pooling outcomes or making live-application claims.
- **Next test:** Exhaustively enumerate small frozen transition graphs, verify that planted cosmetic relabelings pass, semantic differences produce distinguishing traces, incomplete models return `UNKNOWN`, and label/edge mutations are rejected by an independent oracle.
