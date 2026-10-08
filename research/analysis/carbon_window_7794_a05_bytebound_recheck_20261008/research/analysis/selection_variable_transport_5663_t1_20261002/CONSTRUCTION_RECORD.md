# Construction attempts — Issue 5663 T1

- Host attempt 01: pre-provenance construction version; candidate JSON and PASS_METHOD_SCOPED receipt retained, but the shell wrote the two intended exit-file paths into a stray file because of a PowerShell argument-binding mistake. No exact exit receipts were retained. Classified preparation-only with incomplete exit receipts; no formal result.
- Host attempt 02: FAIL before candidate; the construction unit suite exposed the freeze-hash lookup error. Exact failure details retained in construction/host-python311-attempt-02/CONSTRUCTION_FAILURE.txt. Candidate was not invoked in this attempt.
- Host attempt 03: six construction tests passed; candidate CLI exit 0; independent auditor CLI exit 0 / PASS_METHOD_SCOPED. Windows CPython 3.11.9. Raw output, stdout/log files and exit receipts retained in construction/host-python311-attempt-03/.

All host construction runs are distinct from the formally preregistered WSLc allocation. Formal candidate=0, formal auditor=0, retries=0. The initial incomplete attempt and the failure are preserved, not regraded.
