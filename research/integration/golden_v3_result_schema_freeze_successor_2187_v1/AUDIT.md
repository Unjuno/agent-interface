# Audit

This is a conservative schema audit, not an adapter implementation.

The frozen v3 document reports a live route and aggregate measurements: setup/doctor checks, model identifiers and usage, observations, route transitions, submissions, and release evidence. The frozen CLI API provides typed doctor/dispatch receipts and explicitly converts cleanup failure to runtime failure. These are source-backed facts in their respective entrypoints.

The missing proof is the boundary between them. No source-backed machine-readable v3 result object and no explicit adapter were identified in the frozen set. Therefore fields such as task success, useful effect, partial effect, stale invalidation, and per-attempt observation freshness cannot yet be mapped one-to-one to the CLI receipt. The fact that both sides mention related lifecycle concepts is insufficient.

## Acceptance

A future schema-freeze commit can close this HOLD only after it retains:

1. exact source/blob identities;
2. a field-by-field matrix for emitted v3 result data;
3. an explicit typed disposition for every lifecycle state, including partial effect and cleanup failure;
4. proof that task success is not inferred from launcher/program completion;
5. proof that mapping cannot grant side-effect authority;
6. an independent auditor and first-result retention.

No model, GUI, network, input, Docker, or runtime invocation occurred.
