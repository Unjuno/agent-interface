# DRAFT — not submitted; no remote Issue number

Proposed title: Successor #1713/#501: SQL statement-cache lifetime versus per-intent read receipts

This is retrospective delivery of the locally preregistered, completed
`sqlite-readset-cache-20260922-01`, not a new run or a claim of public preregistration.
Preserve all preceding experiments. No wrapper-only Issue is requested for the
retained construction timeout or instrumentation fix.

Scientific question: can compile-time SQLite read callbacks supply fresh
per-intent dependencies on a warm connection? Compare callback-only/cache128,
callback-only/cache0, and connection/schema/SQL-bound dependency metadata plus
fresh revisions on every execution. All authorizer callbacks return SQLITE_OK;
this is authorized, cooperative data-freshness instrumentation, not an
access-control or vulnerability test.

H/T/D/C/U and source/decision chronology are in PLAN.md / REPORT.md. One formal
60-case allocation,10 immutable batches, all exits retained, zero formal reruns.
Results: callback-only misses10 dependencies and publishes2 stale private values;
cache0 has no omissions/stale effects but2 unnecessary refusals; metadata reuse
has0 omissions/stale effects/unnecessary refusals on20 cases. Independent
raw/SQLite audit errors0;8 case-level semantic corruption controls rejected.

No production/shared runtime change, GUI/model/token/latency/security/general SQL
claim. This constrains a concrete source adapter under #1713; broad integration
and repository roadmap remain outside scope. Full raw evidence and original
construction failures accompany the additive patch.
