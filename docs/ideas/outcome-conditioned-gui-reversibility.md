# Uniform versus outcome-conditioned reversibility of GUI actions

- **Status:** Unverified; peer review requests additive provenance and auditor-coverage corrections.
- **Source:** Issue [#7949](https://github.com/Unjuno/agent-interface/issues/7949).
- **Idea:** Compare whether a GUI action is reversible under every possible outcome and one common undo policy, versus only outcome-conditioned recovery, before making planning decisions.
- **Outcome:** Peer review of the retained A05 rows found the scenarios reconstruct, but requested a digest/provenance correction and identified three frozen auditor coverage gaps. Preserve the original STOP and raw bytes and consumed allocations; no candidate rerun is requested. This does not establish safe undo or authorize action admission. See the Issue's review-linked evidence PR [#8297](https://github.com/Unjuno/agent-interface/pull/8297).
