# Live adapter effect scorer v1 (#2246)

This is an additive, read-only scorer for the retained
`runtime/results/golden-desktop-app-server-v3-live-01/golden-report.json`.
It does not modify or replay that report and performs no model, GUI, keyboard,
pointer, network, or input action.

The scorer checks the serialized schema, exact six-task cardinality, cold/reuse/
repair routes, independent exact-count oracle, typed outcomes, exact submissions,
and release/cleanup evidence. A valid report returns `HOLD_NO_MODEL_AUTHORITY`
unless the caller explicitly supplies `--live-authority`; that flag only records
an external gate and never claims the scorer executed a live run. Malformed,
stale, or ambiguous evidence returns `FAIL`.

Formal scope: this PR proves independent scoring of retained serialized evidence
and the fail-closed authority boundary. It does not prove a fresh live run,
repeatability, baseline, rate, generality, or token efficiency.

Pinned source target for the workflow is main commit
`39519f3f3e87626bf2ed6abe7f90e45f8b6878a3`; the workflow records the fetched
report hash and container image digest.
