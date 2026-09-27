# Repository archive replay re-audit (append-only)

This supplements `RESTORE_EVIDENCE.md`; it does not replace the frozen `PUBLICATION_MANIFEST.json`, raw archive, `RESULT.json`, or first outcome.

## Exact archive

Reconstruction from the 35 ordered GitHub blobs `raw-evidence-01.tar.gz.partaa` through `.partbi` produced SHA-256 `49a28fb2a9a84414c10cbf843bef36aa256942bcaad0e9465e16adfef2bad7fd`, matching the frozen publication manifest. The observed archive length is **282,127 bytes**. The old manifest says **282,624 bytes**, a 497-byte metadata discrepancy; preserve both values in the record and do not edit the old manifest.

The tar has 64 members: 30 regular files named by the outer `archived_files` allowlist, 32 `._*` AppleDouble metadata sidecars, and two directory entries. All 30 allowlisted files exist and match their declared SHA-256 values; there are no missing or extra non-sidecar regular files. The raw archive itself remains byte-for-byte unchanged.

## Repository-only replay

1. Concatenate parts in lexical order `aa` through `bi` and verify the archive SHA above.
2. Extract to a disposable staging directory. Keep that exact extracted directory for provenance.
3. Create a fresh audit artifact directory by copying only the 30 paths listed in `PUBLICATION_MANIFEST.json` → `archived_files`. Verify each copied file against its listed SHA-256. This removes only packaging-side AppleDouble files from the *replay directory*; it does not alter the original archive.
4. Run the frozen `audit_task_effect.py` against that fresh directory and the eight source files at commit `01349d7bc76e5635f5568c53ffeec4d9ff49abb1`. The raw-only audit returned `PASS_CHROMIUM_FIXTURE_TASK_EFFECT_SCOPED`, errors `[]`, with all checks true.
5. Run the frozen seven mutation tests. Result: 7/7 pass. Local Windows execution changed only the test module's hard-coded `/out` mount path in an ephemeral copy to point at the fresh artifact directory; test logic was unchanged.

## Disposition and scope

`HOLD_ARCHIVE_SIZE_METADATA_MISMATCH` records the incorrect byte-count field and AppleDouble packaging noise. The scientific one-shot result remains `PASS_CHROMIUM_FIXTURE_TASK_EFFECT_SCOPED`. No new formal allocation, GUI/input session, Docker run, model call, GPU access, retry, or result edit occurred.