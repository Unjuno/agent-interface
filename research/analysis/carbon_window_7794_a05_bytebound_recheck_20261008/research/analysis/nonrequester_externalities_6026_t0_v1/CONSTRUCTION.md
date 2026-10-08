# Construction CI record

- Base main: `722c42bf0d6d808cf80575ecb6353401de934b26` (observed 2026-10-01 before local work).
- Local branch: `research/nonrequester-externalities-6026-t0-20261001`.
- Final host suite: `python3 -B -m unittest -v test_method.py` — 11/11 PASS.
- Candidate host-run-06: exit 0; all 27 event IDs and 7 tasks × 2 routes retained.
- Independent host audit host-run-06: `PASS_METHOD_SCOPED`, 54 executed checks, including per-event recipient/route verification.
- Host-run-05 is retained but reclassified `AUDIT_INCOMPLETE` after a final challenge found duplicate task×route assignments were not independently forbidden and its check count was hard-coded.
- Syntax: `python3 -m py_compile candidate.py audit.py test_method.py` — PASS.
- Whitespace: `git diff --check` — PASS.
- Host-run-01/02/03/05 PASS outputs were subsequently challenged and reclassified `AUDIT_INCOMPLETE`; exact raw and contemporaneous audit outputs are preserved with separate review notes. Host-run-04 candidate did not launch because its output directory was absent. Host-run-06 is the current host method result with runtime-counted checks and assignment-uniqueness controls.
- Container allocation: NOT RUN; reservation requested in shared #5085 queue, not yet authorized.
- Scientific interpretation: method-only synthetic fixture. No human-effect evidence.
