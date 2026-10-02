# Archival qualification — Issue #5537 T7 audit STOP

This is an evidence-only preservation of the three T7 raw/audit/disposition
files from branch tip `3bd3b7bb50da670d5f7eb91894ae691fa6a7cb28`. It does not
rewrite the failed gate or claim a scientific result.

## Disposition

`STOP_AUDIT_MISMATCH`. The retained 135-row base audit reports no base oracle
errors, and the targeted false-admission mutation was rejected. However, only
5/6 preregistered mutation controls were rejected: `false_status` assigns
`GLOBAL_SECTION_CERTIFIED` to a row that already has that value, so it is a
no-op and was not rejected. The preregistered mutation gate failed; no
scientific PASS is accepted. No retry or post-freeze change was made.

## Evidence boundary

The source branch contains only `raw/formal.jsonl`, `raw/audit.json`, and
`raw/STOP_REPORT.md` for T7; the runner, auditor, and freeze are not included in
this packet. The accompanying Issue #5537 T7 record describes one host-local
CPython run and its raw/audit hashes. This archive preserves those recorded
claims without independently reproducing them. It is synthetic only: no
calibrated interface tolerance, GUI, model, task effect, Docker, or production
safety conclusion follows. T5/T6 and T8 remain separate allocations and their
records are not pooled here.

No candidate, test, auditor, or experiment is rerun as part of this archive.
Any further attempt requires a new allocation and non-identity assertions for
every preregistered mutation before freezing.
