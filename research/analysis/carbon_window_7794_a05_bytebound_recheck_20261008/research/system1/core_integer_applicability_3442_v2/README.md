# Issue #3442 v2 — one-shot auditor HOLD archive

The candidate and raw-only auditor each ran exactly once. The candidate emitted
390 rows; the frozen auditor returned `FAIL_OR_HOLD`, despite rejecting all ten
corruption controls, because its accepted-operation row gate requires an
`operation_index` that the runtime only supplies on an operation-level
`ContractError`. The formal outcome therefore remains **HOLD / unresolved**;
no candidate hypothesis PASS or FAIL is claimed.

Original raw, failed audit, process receipt, result report, and sources remain
unchanged. Do not rerun or rewrite either one-shot process. The package's
`LOCAL_CI.json` is preparation-time evidence and predates this formal run.
See [`ARCHIVAL_QUALIFICATION.md`](ARCHIVAL_QUALIFICATION.md) for archive and
local-validation boundaries.
