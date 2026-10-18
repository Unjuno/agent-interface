# Relation-first versus keyword-first cross-domain idea retrieval

- **Status:** Search allocation stopped before candidate rating; hypothesis unevaluated.
- **Source:** Issue [#8073](https://github.com/Unjuno/agent-interface/issues/8073).
- **Idea:** Compare retrieval based on relational structure with keyword-first search for finding cross-domain analogies, while independently judging source validity and relevance.
- **Outcome:** A01 `STOP_SEARCH_SURFACE_BUDGET_NONCOMPLIANT`: one frozen request returned 27 combined hits without auditable query-to-result grouping against a five-per-query cap. No candidates were rated and no assessor panel or formal candidate/auditor ran; the consumed query was not retried. Merged [PR #8293](https://github.com/Unjuno/agent-interface/pull/8293) preserves the search result and limits.
