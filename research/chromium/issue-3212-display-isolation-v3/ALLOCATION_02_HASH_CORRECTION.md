# #3419 allocation 2 — independent raw-byte audit correction

Decision: HOLD_RAW_BYTE_MANIFEST_MISMATCH

This correction is additive and does not modify ALLOCATION_02_PASS.md. Issue #3430 is the successor owner.

## Finding

The allocation-2 container printed a SHA-256 for a serialization whose newline handling was not independently bound to the displayed JSONL bytes. A fresh external reconstruction produced:

- displayed LF JSONL bytes hash: `7f1644cec3139a19775abed57a497e933f776d1bc8f6b2c63fff8f6145ef99f8`
- allocation-2 published hash: `57233e2a13c34c26da7e2176aef55898a0dc66ac80ff1e54e3b529ad3b351f79`
- mismatch: `true`

The gate observations themselves remain retained as historical observations, but the formal raw-byte manifest gate is not proven. Do not treat allocation 2 as a verified scientific PASS.

## H/T/D/C/U

- H: The observed old-target rejection, decoy isolation and p2 effect may reproduce, but exact raw-byte provenance must be bound before acceptance.
- T: Fresh allocation under `research/chromium/issue-3212-display-isolation-v3`; write raw bytes first, hash the exact file bytes, publish those bytes and have an independent container recompute the same hash.
- D: Preserve both hashes, serializer, newline encoding, raw file and audit output. Do not rewrite the prior report.
- C: Any hash mismatch is HOLD/STOP; no broad GUI claim.
- U: No gameplay, multi-application reliability, or product readiness claim.
