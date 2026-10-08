# Local validation — A04

Formal candidate and auditor are not rerun during validation.

- `python -B -m unittest -v` — **9/9 PASS** (post-formal; 0.003 s).
- `python -B -m py_compile candidate.py auditor.py test_protocol.py` — **PASS**.
- `SHA256SUMS` — all listed local files verified before publishing.
- Formal raw-only audit — **9 rows, zero errors, five corruptions rejected**, as recorded in `execution/formal-01/audit.json`.

The tests validate the authored matched fixture, auditor and mutation controls only. They do not establish live cue timing, GUI behavior, or task effect.
