# Construction attempts

`fixture.json`, `candidate.json`, and `audit.json` at this directory's root preserve the first 128-seed construction trial. It passed 3,328-row reconstruction, but its selector-facing and audit-only records shared a trace structure. That design was superseded before formal freeze; its output is retained as construction-only and is not pooled with formal rows.

`attempt_02/` preserves a second 128-seed construction trial with explicit `selector_transcript` and `audit_trace` separation. Its raw-only audit passed all 3,328 rows with zero errors. Formal seeds are disjoint from both construction seed sets. The formal allocation and all decision gates are in the parent `FREEZE.json`.
