# Run record

- Frozen source commit: `7625a3fc99f1da2099dc6e20e67383ee88c7f337`.
- Input archive: five base64 Git blobs, concatenated and decoded in memory; archive SHA-256 and member count verified against the retained evidence manifest. No files were extracted.
- Environment: Windows host, Python 3.12.10 standard library. Docker Desktop service was stopped; this was a read-only archive applicability audit, so no container/runtime was started. No network, GUI, model, game, or input action occurred.
- Pre-run construction: `python -m unittest -v` — 6 passed; `python -m py_compile candidate.py independent_audit.py test_audit.py` — passed; frozen source hashes matched; raw outputs absent.
- Candidate: `python candidate.py` — executed once; `candidate.raw.json` retained.
- Independent audit: `python independent_audit.py` — executed once; 4 rows, zero errors, `PASS_AUDIT_HOLD_CAUSAL_EDGE_PROVENANCE_MISSING`.
- Post-audit construction suite: `python -m unittest -v` — 6 passed. Neither candidate nor auditor was rerun.
- Exact outputs and sources are inventoried in `SHA256SUMS.txt`; the root `.gitattributes` rule preserves exact raw bytes across checkouts.
