# Allocation T0a STOP — pre-candidate freeze integrity

- Disposition: `STOP_BEFORE_CANDIDATE_FREEZE_INTEGRITY_CHANGED`.
- Candidate invocations: 0. Auditor invocations: 0. Retries: 0.
- Frozen source HEAD: `f9fb28932226a0d12c1200f8b9215f7e89993849`.
- Freeze recorded `audit_result.py` SHA-256:
  `a3053eecbcfc538f7b3d1eb81ba824a8aa4165797fb153520868295c62157ef8`.
- The pre-candidate review then found that JSONL event ordering and sorted JSON
  object ordering could differ while representing the same exact event set. The
  auditor was corrected before invocation; its current SHA-256 became
  `d4e951624ef5eeee547429436480d2d21eb6c746622e09931014bdd01434bd9d`.
- The mismatch invalidated the recorded source freeze. `FREEZE.json` and its
  hashes remain unchanged; no candidate was launched under the invalidated
  freeze. Current main advanced to `f44c5f5724ed2ba1d44cab9a8b3f88f5179c014c`;
  governing docs, the research issue index, and paths matching #5865/
  negative-delivery were unchanged in that main delta. Issue #5865 remains open.

The corrected source proceeds only in a distinct additive T0a-A02 package.
This STOP is preserved and is not a scientific result.
