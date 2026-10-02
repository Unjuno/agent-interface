# Archived preparation qualification — Issue #5803

This package preserves the inactive preparation branch `research/mitra-dynamo-bootstrap-4947-v3-20261001` (head `b8f5adbc2eaba69d6b35254292da85c88bdb1868`) as a handoff, not as a formal result. The five files from that branch are copied byte-for-byte; `SOURCE_SHA256SUMS` records their hashes.

## H / T / D / C / U

- **H:** importing `torch._dynamo.external_utils` before Mitra/AutoGluon may avoid the exact partial-module setup failure retained by #4947 v2. The separate natural-mode versus `eval()` mode-drift hypothesis is not tested here.
- **T:** the historical construction fixture substitutes controlled fake `torch`/Mitra modules and checks import ordering. It does not execute real PyTorch, AutoGluon, a GPU, or the pinned container. No formal allocation, container candidate, or raw auditor was run for v3.
- **D:** the branch's historical report records 2/2 synthetic import-order tests and 7/7 inherited #4821 audit-construction tests under CPython 3.11.9. On 2026-10-03, the two checked-in tests were rerun from the recovered source under CPython 3.14.5 and passed 2/2; `py_compile` passed for the three production Python files. These are construction checks only.
- **C:** the fixture mocks the external dependencies; it cannot show that the import repair works in the pinned PyTorch/AutoGluon image or on CUDA. No predecessor STOP or result was rerun, replaced, or pooled.
- **U:** no bootstrap repair, model load, mode-drift outcome, model-quality effect, or runtime benefit is established. The exact GPU/image/source owner allocation remains a prerequisite in #5803/#5085.

## Formal-source HOLD

Issue review identified that the branch's `runner.py` is not aligned with the proposed protocol: it retains the inherited 16 warmups, 1,024 queries, and 16 repeats, emits latency verdicts, does not implement the preregistered 16-query × 4-repeat natural/eval arms with per-module training-state capture and matched RNG restoration, and retains an older allocation ID. The runner is therefore preserved for provenance but is **not approved for formal execution**. Do not interpret the synthetic test PASS as resolution of these gaps.

Current disposition: `HOLD_PREPARATION_ONLY_PROTOCOL_MISMATCH_AND_NO_ALLOCATION`. Issue #5803 remains open. Any future formal attempt requires a new, exact current-main freeze, a corrected reviewed runner, and an explicitly assigned exclusive GPU/container window. All #4947 v1/v2 STOPs and raw evidence remain unchanged.
