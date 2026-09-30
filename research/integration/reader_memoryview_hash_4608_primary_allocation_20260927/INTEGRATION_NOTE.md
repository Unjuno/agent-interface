# Issue #4608 — authorized allocation evidence (relocated)

This directory is a collision-free, byte-preserving relocation of the complete 18-file evidence subtree from PR #4647. Its scientific/source/archive files reuse the original Git blob objects unchanged; `INTEGRATION_NOTE.md` is the only new file.

## Allocation and disposition

- Issue: #4608; authorized one-shot allocation, formal-01; frozen image `sha256:4c2cf9917bd1cbacc5e9b07320025bdb7cdf2df7b0ceaccb55e9dd7e30987419`.
- Primary raw SHA-256: `d11b52ac74f90cc9418b267eacb111d92bc5d1581f7f396544fab0102d5b2da6`. The original evidence ZIP SHA-256 is `91cebf75f5dab6e98cd69fc2eae960ddfc166a503fcca2ac2d571ecd24e4b955`; its `RAW.json` was read back and independently hashed before this relocation.
- The 24 resource and 2 contract workers completed. The preregistered peak-allocation gate did not pass: at cursors 2048 and 4064, candidate and baseline peaks were equal in all three repetitions (median ratio 1.00). Timing guards passed. This is not evidence for adopting the memoryview candidate.
- The formal raw result is distinct from the later `#4651` bundle (`901413b691952c1b3eb9b37996bf13ccf8fadb957f0cd9ffe5b2d58cd98fa518`). Issue #4608 records that later same-schedule run as an unauthorized duplicate; do not pool it with or use it to adjudicate the authorized allocation.
- The primary allocation's post-formal auditor robustness suite rejected 7/10 corruption controls; three malformed cases raised uncaught `KeyError`. Preserve this defect and the original `FAIL` report as-is. No rerun, repair-in-place, or success claim is made here.

## Why the path moved

The original PR #4647 path, `research/integration/reader_memoryview_hash_4451_v2/`, is already occupied on `main` by the later #4651 diagnostic bundle. Directly merging #4647 conflicts with that path and would conflate two distinct raw records. This sibling path separates the authorized primary allocation without rewriting either record. Issue #4608 and broader parent #4451 remain open; the one-shot allocation is consumed.