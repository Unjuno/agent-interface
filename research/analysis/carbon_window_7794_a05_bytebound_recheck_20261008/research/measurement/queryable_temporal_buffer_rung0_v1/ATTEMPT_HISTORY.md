# Construction history

All entries are pre-formal construction findings; no formal/live allocation was consumed.

1. Initial fixed candidate/oracle check exposed non-canonical `unavailable_intervals` ordering when explicit capture gaps and later retention evictions were recorded in different ingestion orders. Repair: canonical chronological ordering at query output.
2. Age-advance adversarial query exposed that retention expiry was enforced only on append. A planner pause with no new capture could return pixels older than `max_age`. Repair: query-time expiry plus future-query/future-anchor rejection.
3. Scope adversarial query exposed that gap receipts lacked session/surface identity, allowing a drop on one surface to contaminate another surface's query. Repair: gaps are scope-bound and filtered by exact session/surface.
4. Long-running stress exposed unbounded gap receipt and event/action anchor metadata even when pixels were bounded. Repair: bounded anchor count+age; bounded exact gap ledger with explicit `GAP_METADATA_OVERFLOW` coverage failure rather than silent metadata loss.
5. After these repairs, the complete fixed/random/exhaustive/metadata-stress construction passed with no candidate/reference mismatch.

No thresholds or scientific success criteria were relaxed after these findings.
