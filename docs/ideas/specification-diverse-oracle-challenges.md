# Specification-diverse challenges for shared oracle omissions

- **Status:** A03 found no incremental value on a finite contract packet; prior coverage HOLDs remain.
- **Source:** Issue [#8088](https://github.com/Unjuno/agent-interface/issues/8088).
- **Idea:** Test whether independently implemented candidates/auditors can share the same error when they rely on one semantic specification, using challenges derived from alternative specification decompositions.
- **Outcome:** A03 `NO_INCREMENTAL_VALUE_SCOPED` on the frozen eight-contract packet: eight baselines passed, 6/6 single-clause controls were rejected, and 15 obligations were reconstructed over 14 rows; no omission difference was adjudicated. A01 `HOLD_BASELINE_ORACLE_COVERAGE` and A02 `HOLD_C02_LIST_IDENTITY_COVERAGE` remain distinct. This neither establishes current repository audits are defective nor treats human adjudication as ground truth. Merged [PR #8204](https://github.com/Unjuno/agent-interface/pull/8204) preserves the result.
