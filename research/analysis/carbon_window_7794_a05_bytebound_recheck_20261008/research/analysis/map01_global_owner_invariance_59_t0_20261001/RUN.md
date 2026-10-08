# Run record

- Environment: Windows host, Python 3.12 standard library; Docker Desktop engine unavailable. No container or live GitHub Actions/API request was started by the candidate.
- Frozen source: `ad123c3875d81ebdc8bdfbdb59340005d705a60d` (workflow and helper identities in `FREEZE.json`).
- Construction: `python -m unittest -v` — 3 passed; `python -m py_compile candidate.py independent_audit.py test_construction.py` — passed.
- Candidate: `python candidate.py` — executed once; output retained in `candidate.raw.json`, SHA-256 pinned before audit in `AUDIT_FREEZE.json`.
- Independent audit: `python independent_audit.py` — executed once; 8 matrix cases, zero audit errors, scoped disposition `FAIL_EVENT_FILTER_ESCAPES_PATH_GLOBAL_OWNER`.
- Outputs are write-once; no retry or modification was performed.
