# Run record

- Frozen repository source: `3021e5ed9bcb4ee36bc4f738c851ec8f9a678cbc`.
- Environment: Windows host, Python 3.12.10, standard library only. `com.docker.service` was `Stopped / Manual`; no container was started or inspected. No network/model/GUI/input action occurred.
- Pre-freeze construction: `python -m unittest -v` — 6 passed; `python -m py_compile candidate.py independent_audit.py test_construction.py` — passed; candidate/audit outputs absent; all source hashes and current-main pin matched.
- Candidate: `python candidate.py` — executed once; raw output retained as `candidate.raw.json`.
- Audit freeze: candidate SHA-256 `a0f781d27da81c9dbc504e1665ea07f6fd275b053291d7885e9a46734db41ba2`; auditor source SHA-256 recorded in `AUDIT_FREEZE.json`.
- Independent audit: `python independent_audit.py` — executed once; six cases, zero errors, `PASS_METHOD_SCOPED`.
- Construction suite rerun after audit: `python -m unittest -v` — 6 passed. No candidate or audit rerun occurred.
- Integrity: `git diff --check` passed before documentation; final file identities are in `SHA256SUMS`.

Outputs are write-once. No retry or substitution was made.
