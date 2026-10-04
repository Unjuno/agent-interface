# V39 A01 read-only audit successor — A02 result

## H/T/D/C/U

- **H:** Re-running the original saved-output auditor writes a fresh verdict into the source archive's SHA256SUMS-covered `raw/AUDIT.json`; V2 can independently check the same saved result without changing the archive.
- **T:** Frozen experiment `V39-READONLY-AUDIT-59-A02-V2-20261005`, source archive at PR #7662 head `719ef679c977a925db3a6d1fe15f9cd93cf2b42c`. The V1 and V2 auditors ran on separate temporary copies. File hashes were compared before/after; a separate test mutated a disposable raw copy and checked that V2 failed without writing.
- **D:** PASS the defect reproduction if V1 exits 0 and changes exactly `raw/AUDIT.json`. PASS the correction if V2 returns `PASS_READ_ONLY_ARCHIVE_AUDIT`, preserves every archive byte, and rejects the tampered copy without additional changes.
- **C:** The A01 scientific projection result remains intact and its values still pass the saved-output reconciliation. The reproduced flaw is in evidence-handling behavior: Windows newline conversion changed the file bytes even though JSON content stayed the same.
- **U:** This is a Windows/Python archive-integrity construction check. It does not test X-server timing, application input consumption, a game, GUI, model, OS input, or task effect.

## Observed result

V1 exited 0 but changed exactly `raw/AUDIT.json`, from SHA-256 `d46a7733360e64271e154f2c0ab9894a114fd6f391574ffe055b09ab2fa7846a` to `8e5980da83ac1b0d8516bb12af8e52937825f2fc2f4781120765616e797b438e`. The write was reproduced only on a temporary copy; the preserved A01 package remained at its original hash.

V2 returned `PASS_READ_ONLY_ARCHIVE_AUDIT`, found the original baseline 4/8 false accepts, candidate 0/8, and the 15/85 baseline/candidate interval sweep, while leaving the disposable archive byte-identical. The tamper control returned exit 1 without further writes. The A01 source/raw artifact itself remains unchanged.

Three unit tests, Python compilation, the frozen mutation probe, and the read-only audit passed. See `RUNS.json`, `MUTABILITY_RESULT_A02.json`, and `out/` for commands and captured outputs. The initial pre-freeze check is retained separately as `MUTABILITY_RESULT.json`.
