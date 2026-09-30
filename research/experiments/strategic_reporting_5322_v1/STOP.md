# STOP — formal allocation not started

Formal execution did not start. During pre-allocation GitHub readback, the preregistered SHA-256 values did not match several files published on the branch. The GitHub Contents API readback has now been recorded in `FREEZE.json` for traceability, but this discrepancy invalidates the planned source freeze. No formal seeds/cells were consumed and no result is claimed. Do not trigger `START_FORMAL.txt` from this source state.

The next safe step is to reconstruct and hash the exact repository bytes, correct the manifest on a fresh successor branch or create a versioned v2 source, rerun construction checks, and freeze it before allocation. Local C: has 0 bytes free, so current local mirrored sources and fixtures cannot be safely written or verified.
