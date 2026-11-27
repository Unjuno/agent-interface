# Scoped infeasibility feedback for GUI plan backtracking

- **Status:** Synthetic method result passed; GUI transfer remains unverified.
- **Source:** Issue [#8473](https://github.com/Unjuno/agent-interface/issues/8473).
- **Idea:** Test whether a bounded local feasibility checker can return typed, source-scoped reasons that prune only an affected symbolic GUI-plan branch and request an alternative.
- **Outcome:** A02 independently reconstructed 21 symbolic policy rows, rejected 5/5 mutations, and passed 8/8 construction plus 3/3 archive-closure checks. It complements the separate four-case/12-row fixture in PR #8475. The evidence does not show that screenshots support sound impossibility predicates, and grants no runtime authority. Merged [PR #8480](https://github.com/Unjuno/agent-interface/pull/8480) preserves A02.
