# Provenance-bound object memory

- **Source:** Open [Issue #7167](https://github.com/Unjuno/agent-interface/issues/7167); synthetic T0 retained by merged [PR #7523](https://github.com/Unjuno/agent-interface/pull/7523).
- **Status:** `PASS_METHOD_SCOPED` for one deterministic data-transformation contract. No live vulnerability, model compliance, or security guarantee was tested.
- **Related question:** [#8618](https://github.com/Unjuno/agent-interface/issues/8618) asks whether private cross-task information can influence an otherwise authorized public action at admission. That is a separate action-boundary evaluation; #7167 tests provenance retention and authority projection through a synthetic memory pipeline.

## Idea

Persistent object or scene memory can retain application-rendered instructions. If later retrieval presents them as trusted user intent, descriptive content has crossed an authority boundary. Preserve origin and semantic class through storage, summary/consolidation, and retrieval: for example, `USER_INSTRUCTION`, `APPLICATION_CONTENT`, `OBSERVED_EFFECT`, `MODEL_HYPOTHESIS`, `DERIVED_SUMMARY`, and `VERIFIED_SYSTEM_FACT`. Memory may inform reasoning, but a label cannot itself authorize an action. Target, lease, and effect checks remain independent.

## T0 result

The frozen host-only standard-library candidate and independent auditor each ran once. They reconstructed 10 synthetic records, 3 application-content summaries, and 13 retrieved rows. Only two source-bound user instructions appeared in the active-intent projection; for the conflicting draft key, the latest bound revision remained active. Application text, model hypotheses, derived summaries, missing-source records, and the superseded user revision were not promoted.

The auditor rejected all four planted corruptions: promote application content, drop summary provenance, resurrect an older user revision, and trust a missing-source record. The package tests pass 3/3 and the ten-file SHA-256 manifest verifies. Exact report and raw artifacts are retained in the [T0 package](../../research/analysis/provenance_memory_authority_7167_t0_20261004/REPORT.md).

## Limits and continuation

This proves only that the tested deterministic pipeline preserves stipulated labels and authority classes, assuming the source and origin labels are authentic and correct. It does not test whether a model follows those labels, whether an application can spoof provenance, or whether a real memory store is vulnerable. Any model or prompt-injection study requires a distinct, separately authorized design. Keep #7167 open as a proposal for that next question; do not merge its synthetic pass with #8618's action-admission estimand.
