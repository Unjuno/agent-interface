# Issue #6575 — observation-transform injection T0

Finite model-free construction check for a source-preserving presentation assay. It compares FULL, FULL+CONTEXT_CROP, CROP_ONLY, and same-dimension FULL+SHAM_CROP over six deterministic synthetic PPM scenes: three stipulated content classes (benign, untrusted-instruction signature, visual distractor) × two panel layouts.

T0 checks image-byte provenance, deterministic crop geometry, unchanged user-content pixels, legitimate target and required safety-cue visibility, matched crop dimensions, and rejection of crops that omit either required region. It does not contain legible attack text, call a model, score proposals, or demonstrate prompt injection. No model credentials or external effect are involved.

Formal receipts and limits: [`formal_01_20261002/REPORT.md`](formal_01_20261002/REPORT.md). Preregistration and immutable source hashes: [`formal_01_20261002/PREREGISTRATION.md`](formal_01_20261002/PREREGISTRATION.md) and [`FREEZE.json`](formal_01_20261002/FREEZE.json).

Allocation 01 ended `STOP_HARNESS_FIXTURE_MISMATCH`: the independent auditor reconstructed all 36 image items but rejected six sham-crop pixel-provenance rows because the frozen oracle's sham coordinates differ from the candidate's. This is not a scientific result about visual prompt injection; the failed allocation is retained without retry.
