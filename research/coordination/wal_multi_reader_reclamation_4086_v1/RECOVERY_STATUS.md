# Recovery and evidence-delivery status — 2026-10-01

## Disposition

`STOP_FORMAL_EVIDENCE_ARCHIVE_INCOMPLETE`. Preserve all original files and the historical reported result, but do not claim the 12-case formal result has been independently revalidated. The consumed formal allocation was not rerun or replaced.

## Read-only recovery checks

- The pre-formal capsule reconstructed from `preformal-source-00.b64` and `preformal-source-01.b64` is 9,220 bytes and has SHA-256 `d41254654872439641aa20132b52da795277408da370cc8978381032baab882c`, matching `PREFORMAL_SOURCE_MANIFEST.json`.
- The frozen `FREEZE.json` blob has SHA-256 `0c6e70f30620f1c2188c4a5b37d363308cc2a2ff2ef73d2707958e4f14f6ade7`, matching `PREFORMAL_SOURCE_MANIFEST.json`.
- `PACKAGE.json` requires five chunks (00–04) of 50,000 / 50,000 / 50,000 / 50,000 / 13,884 base64 characters and declares a 160,412-byte archive.
- The committed `evidence_parts/` instead contains 18 chunks (00–13 and 15–18; 14 is absent), totaling 149,116 file bytes. The first five available files are 6,001 / 6,001 / 6,001 / 9,001 / 9,001 bytes and their SHA-256 values do not match the five hashes in `PACKAGE.json`.
- Running the retained `unpack.py` against the committed parts stopped at `archive hash`, before creating the destination or extracting members. No formal raw archive, expansion, or raw-only audit is claimed.

The mismatch is not safely repairable by renaming or concatenating the available pieces: their bytes do not satisfy the committed package's lengths or hashes, and a chunk is missing. Do not fabricate missing data or substitute another allocation. If the original exact archive becomes available, verify its declared archive hash, file count/expanded size, member safety, freeze/source linkage, and independent raw-only audit before changing this disposition.

## Scope boundary

This recovery verifies only the separately published pre-formal source capsule and freeze digest. The reported finite-model PASS, its 780 checks, and its corruption controls remain historical claims because the raw corpus is unavailable for reproduction. No Docker/container construction result is asserted here; a previous Docker construction-test run was explicitly classified out-of-sequence under the resource gate. No production, runtime, GUI, or task-benefit claim follows.
