# Calibrated recovery deadlines for transient soft signals

- **Status:** Synthetic method passed; no advantage over a fixed timeout was shown.
- **Source:** Issue [#8024](https://github.com/Unjuno/agent-interface/issues/8024).
- **Idea:** Test whether a calibrated recovery deadline can distinguish a transient soft prediction-error excursion from genuine failure while a hard safety monitor remains unconditional.
- **Outcome:** A01 `METHOD_PASS_SCOPED` on an authored deterministic fixture; nominal recovery coverage was 9/9 with no delayed hard events. The calibrated deadline equaled the fixed timeout (9), so the added method showed no advantage over that simpler control. No empirical exchangeability, live GUI, or safety claim. Draft [PR #8036](https://github.com/Unjuno/agent-interface/pull/8036) retains the evidence.
