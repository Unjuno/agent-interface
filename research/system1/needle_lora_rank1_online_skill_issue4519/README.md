# Rank-1 online LoRA skill update

Issue: [#4519](https://github.com/Unjuno/agent-interface/issues/4519), successor to [#4507](https://github.com/Unjuno/agent-interface/issues/4507). Parent evidence: [#3911](https://github.com/Unjuno/agent-interface/issues/3911).

This frozen CPU-only study compares paired rank-1 and rank-2 online adapters on one synthetic skill. It measures held-out accuracy after each feedback arrival and the cost of the eight updates performed at that arrival. The role router uses an immutable base for A, a versioned adapter for B, and YIELD for unknown, stale, future, or missing skill state.

- Protocol: `PREREGISTRATION.md` / `PREREGISTRATION.json`
- Runner: `runner.py`
- Independent auditor: `audit.py`
- Host Docker orchestration: `formal.py`
- Construction-only checks: `test_construction.py`

No product/runtime code or prior result is changed. Formal output is retained in a separate output mount and added to the same allocation branch only after the independent audit.
