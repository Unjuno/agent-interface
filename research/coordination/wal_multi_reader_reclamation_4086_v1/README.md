# Research evidence for Issue #4116

This directory retains the prospectively GitHub-frozen source plus the first formal result. Do not rerun consumed formal batches. `REPORT.md`, `RESULT.json`, `AUDIT.json`, and `FREEZE.json` are directly readable.

The exact pre-formal source/environment/auditor bytes are in `preformal-source-00.b64` and `preformal-source-01.b64`. The complete construction/formal corpus is in `evidence_parts/*.b64`; run `python -B unpack.py <fresh-destination>` to reconstruct it for read-only audit. The complete archive SHA-256 is `22c8e00ec502c6afe290ef1b78d953ad7fa7ad834a729050b3dabe859fe10c6a`.

Scientific result: `PASS_MULTI_READER_RECLAMATION_BOUNDARY_SCOPED`. This is research evidence only, not a runtime/default/product promotion.
