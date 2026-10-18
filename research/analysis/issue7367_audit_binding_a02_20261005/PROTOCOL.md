# Issue #7367 A02 — retained-evidence freeze-binding audit

## Question and hypothesis

Does the A01 auditor bind the candidate's self-reported workload digest to the workload bytes frozen in `PRE-RUN.json`? H: it does not; a post-freeze workload mutation that is reflected consistently in the candidate RAW can pass the legacy audit. A read-only successor auditor must compare the actual workload bytes to the frozen SHA-256 and must retain the original A01 result unchanged.

## Scope and method

Audit only. The candidate (`run_a01.py`) is not invoked. The retained A01 source, PRE-RUN, workload, RAW and original AUDIT are inputs; all are preserved byte-for-byte from PR #7515 head `543561e1721656d4944219d7ae611e285527a54f`. The source's declared frozen hashes for `run_a01.py`, `audit_a01.py`, and `workload.json` are checked before interpreting the result.

Construction controls use disposable copies only: (1) unchanged retained bundle, (2) modify a payload on a record A01 classifies dead, then update RAW's workload digest and canonical record digest. The legacy auditor is expected to accept control (2); the new auditor must accept (1) and reject (2) specifically on the PRE-RUN workload digest binding. These controls are unit tests, not amendments to the frozen A01 files.

Formal invocation: run the versioned read-only A02 auditor exactly once against the retained A01 RAW and unmodified source bundle. Host Python is acceptable for this audit-only check; no candidate/runtime/container claim is made. Do not rerun candidate or alter A01 records. Exit 0 means checks passed; JSON stdout is retained as `formal-audit.stdout.json`.

## Decision and limits

- `PASS_RETAINED_BYTES_SCOPED`: all frozen source/workload digests match, the retained RAW agrees with those bytes, the independent frozen continuation enumeration is retained, and canonical records match.
- `FAIL_FREEZE_BINDING`: any frozen workload/source or retained-record binding fails.

This checks a specific audit-integrity gap only. It does not invalidate or rewrite A01's method-scoped result, assert open-world graph completeness, or establish a model/runtime/product benefit. A01 `PRE-RUN.json`, `RAW.json`, and `AUDIT.json` are evidence and remain immutable.

## Provenance

- Parent result: Issue #7367, PR #7515; original readiness STOP remains preserved.
- Retained A01 source commit: `543561e1721656d4944219d7ae611e285527a54f`.
- Formal machine: Windows host, CPython 3.12.10, local read-only analysis of the retained bundle; no Docker/WSLc operation was part of A02.
- TDD controls: `python -B -m unittest -v test_audit_v2.py`.
