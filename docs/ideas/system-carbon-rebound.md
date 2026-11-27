# System-carbon rebound under endogenous GUI-agent demand

- **Status:** Synthetic accounting-method result passed; empirical effect is unmeasured.
- **Source:** Issue [#8421](https://github.com/Unjuno/agent-interface/issues/8421).
- **Idea:** Test whether lower per-effect energy can increase session-total operational carbon when reduced interface cost causes more work to be requested or completed.
- **Outcome:** T0 `PASS_METHOD_SCOPED` for synthetic accounting arithmetic. In a seeded sign-reversal case, client energy per effect fell from 9,000 J to 3,840 J while session operational emissions rose from 6 g to 9.1 g CO2e as safe effects increased from two to three. This does not measure real energy, grid intensity, hardware, providers, GUI behavior, or user demand. Merged [PR #8430](https://github.com/Unjuno/agent-interface/pull/8430) preserves the finite method package; any empirical eligibility remains separate.
