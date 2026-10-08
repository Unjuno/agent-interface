# Issue #8073 real-corpus retrieval A01

**Terminal disposition: `STOP_SEARCH_SURFACE_BUDGET_NONCOMPLIANT`.** The relation-first versus keyword-first hypothesis is **UNEVALUATED**.

The pre-frozen protocol specified eight open Issue targets, paired one-query budgets, at most five results per query, candidate lineage, blinded independent ratings, and an independent audit. A single search request submitted both arms for two targets (#8166 and #7831). The search tool returned 27 visible results in one combined response, exceeding the allowed maximum of 20 for four queries and omitting reliable per-query grouping. The corpus snapshot and candidate lineage therefore could not be reconstructed. The remaining six targets were not searched. No candidates were rated, no assessor panel was used, and no PASS/FAIL inference was made.

The four queries are consumed; no retry or post-hoc tool substitution occurred. See [`PROTOCOL.md`](PROTOCOL.md), [`RUN_RECORD.md`](RUN_RECORD.md), and [`STOP.md`](STOP.md). A valid successor needs a versioned fixed corpus and an execution interface that enforces and records each per-query cap.

This STOP does not alter the synthetic pipeline-sensitivity result in PR #8238 and does not establish external search superiority, idea quality, or research productivity.
