# Research evidence for Issue #4116

> **Recovery status (2026-10-01): `STOP_FORMAL_EVIDENCE_ARCHIVE_INCOMPLETE`.** The pre-formal source capsule is recoverable, but the formal archive is not: the published evidence parts do not match `PACKAGE.json`, and `unpack.py` rejects them at the archive-hash check. Treat the PASS below as the historical reported disposition only; its formal raw evidence and audit have not been independently revalidated. See `RECOVERY_STATUS.md` before using this package.

This directory retains the prospectively GitHub-frozen source plus the first formal result. Do not rerun consumed formal batches. `REPORT.md`, `RESULT.json`, `AUDIT.json`, and `FREEZE.json` are directly readable.

The exact pre-formal source/environment/auditor bytes are in `preformal-source-00.b64` and `preformal-source-01.b64`. Their declared 9,220-byte archive is recoverable. The construction/formal corpus is **not** currently reconstructable from `evidence_parts/*.b64`; do not treat the historical archive SHA-256 `22c8e00ec502c6afe290ef1b78d953ad7fa7ad834a729050b3dabe859fe10c6a` as verified against the available pieces.

Scientific result: `PASS_MULTI_READER_RECLAMATION_BOUNDARY_SCOPED`. This is research evidence only, not a runtime/default/product promotion.
