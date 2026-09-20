# Reproduction and handoff

The exact allocation-02 runner and auditor commands are retained in [formal-02/CONTAINER_RUN.md](formal-02/CONTAINER_RUN.md). They document the historical execution and are **not** authorization to repeat allocation 02 with the same identity.

For independent verification, an integration worker should:

1. Recompute the source, raw, request/report, and audit hashes from the committed bundle.
2. Run the corrected read-only evidence-binding audit from [audit-v2-successor-02/CONTAINER_RUN.md](audit-v2-successor-02/CONTAINER_RUN.md) with the source and evidence mounts read-only.
3. If repeating the experiment itself, create a distinct successor path and allocation identity, preregister new H/T/D/C/U and a complete dependency/source freeze on Issue #3711, use a fresh output directory, and retain any STOP/FAIL unchanged. Do not relabel or overwrite formal-01/formal-02.

Scope to recheck: the CLI producer reports a full write and exit code 0, while a synthetic downstream sink truncates delivery and a JSON parser rejects it. The retained `attempt-status` recovery is read-only. Whether actual integration callers reject malformed stdout rather than trusting only process exit status remains open.
