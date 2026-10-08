# Issue #5024 reconciliation — final state (2026-09-28)

The original reproduction receipt remains immutable at commit `465f3773da73a802d8f4cadeb5316f452e65a6c5`. It accurately records what was known when written: Windows Git rejected the 48 backslash-containing paths; the exact requested frozen commit checkout did not reach its HEAD gate; GitHub MCP tree edits failed; no repair PR yet existed.

## Resolution verified on GitHub

- PR #5032, “Repair Windows checkout paths while preserving frozen evidence identities”, merged to main as merge commit `4c99c8db95afbda58911b69800afc4bbe0c07215` (2026-09-28 05:04 JST).
- The PR maps and renames all 48 images into `results/formal01/corpus/`, preserves their Git blob identities and SHA-256, and records hashes for all 21 non-image study files. It does not rerun or alter the frozen scientific result.
- The recorded local Windows validation used candidate tree `eb0abc591512f91db7ab7b2cdc6c5854e9d1c0c2` in a clean parentless snapshot and reports successful checkout, the migration verifier, and 109 CLI/API/distribution tests (2 skipped). The attached local logs preserve preceding failed partial-clone/long-path attempts and the successful `core.longpaths=true` checkout.
- Hosted checks on candidate commit `dafcbbbd21736bc03c63793c31ebd7c9ecb1ccd3` passed:
  - Runtime unified CLI: Windows, Ubuntu, macOS all succeeded. On Windows, checkout, compile, CLI/API tests, and doctor all succeeded.
  - Portable runtime zipapp: Windows, Ubuntu, macOS all succeeded. On Windows, checkout, compile, distribution tests, build, and artifact upload all succeeded.
- Main readback confirms `verify_path_migration.py` and `PATH_MIGRATION.md` are present. The verifier correctly resolves manifest entries relative to the study directory.

## Independent check and correction

I independently extracted the 48 frozen image blobs and verified their SHA-256 values against `corpus_manifest.json`: 48/48 matched, zero mismatches. My earlier review incorrectly claimed the verifier's root/path join duplicated `results/formal01`; that was a misread. I posted a correction on PR #5032 and this Issue. The migration verifier is correct, and the false-positive review is retracted in the PR conversation (GitHub does not allow dismissing a COMMENTED review).

## Scoped disposition

The Windows portability issue is resolved and integrated. This establishes byte-preserving path migration and passing affected hosted Windows checkout/tests, not any new GPU/scientific finding. The original failed-checkout reproduction and strict-base setup limitation remain historical evidence; they are not overwritten or relabeled.
