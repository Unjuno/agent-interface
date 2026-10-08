# Recovery review: Issue #4037 concurrent compaction prefix

## Disposition

Recover the completed, frozen #4037 formal allocation and all eight lossless archive parts from the stale branch into current `main`. The 18-case formal allocation is consumed and is not rerun.

## H/T/D/C/U

- **H:** A compactor that deletes beyond its captured prefix can remove a newly accepted receipt; prefix-bounded deletion preserves it, while transaction-local frontier revalidation can safely defer maintenance.
- **T:** Verify all eight archive chunks against `PACKAGE.json`; assemble the exact 44,792-byte archive; restore and verify all 776 members; replay the unchanged raw/SQLite auditor and run the retained unit suite. These are evidence reproduction checks, not another concurrency experiment.
- **D:** `PASS_CONCURRENT_COMPACTION_PREFIX_SCOPED`; 18 cases, 54 independent database-copy probes, 90 worker processes. The raw audit reproduced byte-for-byte with `errors=[]`; all 10 corruption controls rejected; all 10 unit tests passed. `STALE_DELETE_ALL` admitted the rebound old identity in 2/6 cases, while both candidate policies had 0/6; each candidate admitted genuine next work in 6/6. `REVALIDATE_FRONTIER` deferred two changed-frontier maintenance operations without mutation.
- **C:** Only the frozen SQLite same-epoch cooperative-issuer model and specified transaction boundary are covered. The separate auditor is same-author, not independent human review.
- **U:** Construction-0 timeout (7 complete, 1 partial, 1 unstarted) remains preserved and excluded. No Docker/OrbStack replication, model/provider, GUI/input, power-loss, natural race rate, timing/token benefit, runtime, or production claim is established.

## Byte and local verification

All eight chunk lengths and SHA-256 values match `PACKAGE.json`; assembled archive SHA-256 is `4e8c5c66c0401eaaecdb6afb043fa7a6125de5e44e1f40a5dd8295634418ebdf`. Extraction restored 776 files / 9,627,357 member bytes. Replayed audit exactly matches retained `AUDIT.json` (SHA-256 `6d0686164a8a7fc59fc672af16746e63d40ed7dbb7414e16a6d649445025743c`); errors are empty, 10/10 controls rejected, and 10 unit tests pass.

## Integration boundary

All files stay under `research/coordination/intent_gc_concurrent_prefix_c84d_v1/`. Historical construction timeout, raw rows, and limits remain unchanged. The original branch is removable only after checks pass, every recovered blob is confirmed on `main`, and no open PR still uses that branch.
