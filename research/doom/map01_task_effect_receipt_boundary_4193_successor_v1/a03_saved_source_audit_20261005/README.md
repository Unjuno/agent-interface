# A03 — independent saved-source audit

This package independently reconstructs the retained #4193 source summary without using the malformed v3 `RESULT.json` or importing its runner/auditor. It confirms six sessions, 194 typed scorer samples, three attack DOWN/UP physical joins, and zero observed positive endpoints in either attack or no-input samples.

**Disposition: `HOLD_NO_POSITIVE_SCORER_EVENT`.** The audit supports only the contents of this immutable saved corpus. It does not establish that an attack caused a task effect. Producer records have no `source_event_id` or `scorer_event_id`; the raw source itself was stored as arrays of JSON strings, which this auditor decodes before traversing nested fields.

The exact v3 `RESULT.json` remains 1,923 bytes with SHA-256 `6f6188814bbbb5aea6bd791a096c1938c2a920da9a0f993d27b491bcb6bcdaf7` and remains invalid JSON. It was not read as an oracle, repaired, or replaced. Original raw bytes also remain unchanged.

This was a read-only host-CPU audit of retained data. No candidate, prior auditor, game, model, GUI, OS input, network service, container, or allocation was invoked. The scope limits in [PLAN.md](PLAN.md) remain controlling.
