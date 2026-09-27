# Issue #3994 — preserved incomplete allocation

Disposition: STOP_OUTER_TOOL_TIMEOUT_PARTIAL. The one monolithic invocation retained
49 complete rows but no outer process return receipt or END.json. Do not infer a
scientific PASS or rerun/resume this consumed allocation. Partial raw SHA256:
`42a28e0ffb2c5d18c3a8a5ecaf89302c156abd28d938bce8e8628e65f5b520e5`.

The source hash freeze in this directory remains unchanged. Complete frozen source,
construction, partial raw, start marker and STOP.json are losslessly retained as
`v1/` inside the [successor evidence bundle](../intent_version_wire_3442_v2/README.md).
Its separate `v2/` allocation belongs to #4009, uses bounded orchestration and fresh
132-case data, and pools none of this predecessor's49 rows. The absence of the old
terminal receipt is preserved, not retrospectively repaired.
