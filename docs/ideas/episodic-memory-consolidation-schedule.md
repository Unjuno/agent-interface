# Schedule sensitivity of episodic GUI-memory consolidation

- **Status:** Proposal remains unverified; A19 is not frozen and was not run.
- **Source:** Issue [#8406](https://github.com/Unjuno/agent-interface/issues/8406), companion to [#7418](https://github.com/Unjuno/agent-interface/issues/7418).
- **Idea:** Hold the ordered source-bound episode stream fixed and compare consolidation timing to test whether update cadence changes downstream memory utility and retention of rare conditions.
- **Outcome:** The latest PR #8545 adds model-free calibration for the A19 decision threshold. Exact enumeration agreed with the Monte Carlo estimates within the preregistered five-standard-error tolerance; reported exact gate rates for +0.10 were 34.5737% (IID) and 49.7283% (fully clustered), and for +0.20 were 92.8598% and 65.4230%. This checks the stated independent-Binomial calibration model only. Qwen answer dependence, GUI task effects, and memory behavior remain unmeasured; A19 remains `NOT_FROZEN_NOT_RUN`. PR #8545 is open Draft with checks and non-author review incomplete.
