# Recovery status — #4362 m6r1

This note is repository-delivery metadata added after the original frozen allocation. It is not part of `FREEZE.json` and does not change any frozen source, gate, input, or outcome.

## Preserved from the original branch

- Original branch head: `6a9386aad7ce7d19c901099e3030473d6612feb2`.
- Exact source, plan, environment, baseline, schedule, upstream reference copies, and three frozen input-archive parts are preserved byte-for-byte under this directory.
- `FREEZE.json` SHA-256: `34f2f4ca836e8cd62bb00b82a577861b7bd22cda32439566982e0423c9813fa0`.
- The input-restoration script verifies archive SHA-256 `e70a610316942517228f33fedecc1c3d33c5dd7391271cd349e984f955162075` and the 12 member hashes. It writes only the requested destination and reports that it did not execute the measurement.

## Formal-result boundary

Issue #4362 records a later `PASS_STREAMING_O2_MEMORY_SCOPED` outcome and identifies its raw audit/control digests. The original branch ref, however, contains only the preformal source/input freeze; its README says formal execution was 0/12 at that commit. The two GitHub Actions runs attached to that branch expose no downloadable artifacts. The formal raw package and result/audit/control files are not included here, and this PR does not reconstruct or independently validate the reported formal outcome.

Accordingly, treat the formal PASS as an Issue-reported historical result pending exact raw-package recovery and read-only audit. Do not rerun the consumed allocation, infer raw rows from the Issue summary, or treat this source-preservation merge as formal-result publication. Keep Issue #4362 open and retain the original branch until the result-delivery dependency is resolved.

## Recovery-only local checks

On 2026-10-02, the frozen six-method construction test suite passed on macOS arm64 / CPython 3.14.5, and `restore_inputs.py` verified and restored all 12 frozen input members (102,297 bytes). Python syntax compilation passed. These checks validate source construction and input packaging only; they are not the frozen Linux/CPython 3.13.5 formal allocation and make no memory/performance claim.
