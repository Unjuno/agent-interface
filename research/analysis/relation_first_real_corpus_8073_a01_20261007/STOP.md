# Issue #8073 A01 — STOP

**Disposition:** `STOP_SEARCH_SURFACE_BUDGET_NONCOMPLIANT`
**Hypothesis:** UNEVALUATED; this is not `FAIL_METHOD`.
**Allocation:** `RELATION-FIRST-8073-REAL-CORPUS-A01-20261007-01`
**Frozen source:** commit `9fb2dd6782d1d1477a00d14be870487fd4c54fa2`
**Run record:** [`RUN_RECORD.md`](RUN_RECORD.md)

The four one-shot queries for targets #8166 and #7831 were submitted together. The tool returned 27 visible results in an unpartitioned response, exceeding the frozen per-query maximum of five and preventing reliable query-to-result lineage. No other target was searched. No candidate, rating, assessor, or hypothesis decision was produced. The queries are consumed and will not be retried under A01.

The failure is in the selected search surface's response/budget contract and corpus snapshotting, not in either retrieval method. A new attempt requires a separately preregistered allocation with a fixed versioned source corpus and an auditable interface that enforces per-query result limits and preserves lineage. The original synthetic evidence in #8238 and this STOP remain separate and unchanged.

No search candidate is being recommended or validated by this record. No external literature, Agent Interface behavior, user outcome, or productivity claim follows.
