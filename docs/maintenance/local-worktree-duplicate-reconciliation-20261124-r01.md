# Root worktree duplicate reconciliation r01

Captured 2026-11-24 against current main
`8886f8eeb05d0c02775dbb80abe10307dd05f289`. Source checkout is the registered
root `main` worktree at `897f4896d23dd127a4523dc4955e573dace7d674`.

For each listed directory, every local file was compared byte-for-byte with
`git show origin/main:<same repository-relative path>`. The tree fingerprint
is SHA-256 over sorted records `UTF8(path) + NUL + lowercase-SHA256(file) + LF`.

| Root untracked directory | Files | Bytes | Current-main match | Tree fingerprint |
| --- | ---: | ---: | --- | --- |
| `research/integration/standard_mcp_task_ledger_57_v1/current_main_calc_failure_recheck_20261121` | 455 | 1,012,906 | 455/455 identical | `298697eb102be2303b3d48f23caa0802c7be0b1db10a7813a097fee06b8b78d1` |
| `research/integration/standard_mcp_task_ledger_57_v1/effect_receipt_handoff_current_main_recheck_20261123` | 5 | 34,370 | 5/5 identical | `d03d2ed27c17dd9a9c0ae789113f3e6a79bc96cfa05009a1a6bd0dbf09afa2e4` |
| `research/integration/standard_mcp_task_ledger_57_v1/pr10218_supersession_audit_20261121` | 6 | 14,592 | 6/6 identical | `d177e8d6df4764be767666ee8bf4a11bb3df9fe58e87228cff08f4d33e9eec7a` |

These are verified local duplicates of main: **466 files / 1,061,868 bytes**.
The #10218 packet is also protected by its own `SHA256SUMS` manifest. A local
recursive removal of that six-file copy was attempted only after verifying its
main counterpart, but the execution policy rejected the operation before it
ran. No local files were removed. Keep the copies and classify them as
`PRESERVED_DUPLICATE_CANDIDATE` until a supported cleanup operation is
available; do not bypass the rejection.

## Preserve for further review

- `calc_save_controller_receipt_order_20261121/`: 17 files; 15 differ from
  current main and 2 have no same-path main file. This is not a duplicate.
- `issue57-next-integration-seam-20261121.md` and
  `open-pr-delta-20261121-r155.csv`: absent from current main.
- `repository-inventory-recheck-20261121-r155.md`: same path exists on main,
  but its bytes differ; retain until its historical corrections are compared.
- Nested `.worktrees/` and `worktrees/` contain registered worktrees and were
  not recursively expanded or modified by this reconciliation.

This is a content-custody classification only. It does not assert that the
root worktree is clean, that the remaining changes are correct, or that Issue
#57 is complete. The root checkout and Issue state were unchanged; this report
is a separate documentation-only branch. The Calc packet follow-up is recorded
below; the root-only post-merge files and three documentation/inventory
remnants still need lineage review.

## Follow-up: restore the frozen Calc R01 manifest bytes

The non-duplicate packet review found a real custody defect in the checked-in
R01 base packet. At the above main revision, only 4 of its 14 `SHA256SUMS`
entries matched the Git blobs because the packet had no directory-wide
no-text rule. A clean registered R01 source worktree
(`codex/issue57-calc-fixture-r01`, HEAD
`bdd1fb57720ab05d671c81dd953e71ad0a70b98b`) supplied byte-exact copies for all
14 entries: every source file matched the existing expected SHA-256. Those 14
files were restored into this current-main candidate and the existing
manifest now passes 14/14. A directory-level `.gitattributes` rule preserves
their bytes on future checkouts; the current-main R02 subpacket retains its
separate, already present raw-byte rule, and its own manifest also passes
11/11.

This changes no runtime or test result. The different root-only
`conditions.json`, `post-merge/RESULT.md`, and `post-merge/artifact-optimized.stderr`
were left untouched; the conditions file did not match either checked-in
manifest and the post-merge records need separate lineage review. The root
copy remains preserved.
