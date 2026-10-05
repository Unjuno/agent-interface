# Saved-only verification

This archive contains inert `.py.txt` source images. Do not run the candidate or an old systemd unit/output to recheck evidence. The frozen candidate ran once. The formal/live-game lane remains separate.

From the repository root, use Python with Pillow and a fresh output directory:

```bash
verification_dir=$(mktemp -d)
package=research/doom/v15_native_executor_59_e0cc_20261005
cp "$package/audit_executor.py.txt" "$verification_dir/audit_executor.py"
cp "$package/audit_mutations_delta.py.txt" "$verification_dir/audit_mutations_delta.py"
python3 "$verification_dir/audit_executor.py" "$package/run-01/raw.json" "$package/source-lock.json" "$verification_dir/audit.json"
# Expected exit 1: frozen audit FAIL, only_loopback; 337/338 original checks.
python3 "$verification_dir/audit_mutations_delta.py" "$package/run-01/raw.json" "$package/source-lock.json" "$verification_dir/mutations.json"
# Expected exit 0: 8/8 add semantic failures beyond unchanged only_loopback baseline.
```

These commands write only into the new directory. Original raw and audit files are read-only inputs. The original `audit_mutations.py.txt` is preserved but was not invoked; do not use its naive any-failure criterion to claim useful negative controls on a failed baseline.

To verify candidate source provenance, fetch the immutable source commit `daa156edd8df541dfe0192c3f6f0c69b36b92fa2` from origin (or fetch current refs/pull/8094/head and verify that this exact commit exists in its history). Read every `source-lock.json` path via `git show <immutable SHA>:<path>`, and compare both blob identity and SHA256. Do not require the moving PR tip to equal the historical source commit or substitute a new tip. All source images were preserved in Git; the archive does not duplicate the 81-source closure.

`manifest.json` binds every other archive file and excludes itself. It records inert `.py.txt` filenames; their bytes equal the names in `freeze.json` without the final `.txt`. `execution-record.json` records actual commands and exits. Network diagnostic v2 is a different no-input namespace observation; it is not a replay or retrospective proof of the candidate's missing interface state. Actual runtime package versions are in environment-result.json. Resource, transfer and VM-stop receipts are included. No game, model or candidate rerun is required for saved verification. Saved-raw checks need no network access; source provenance verification needs a Git fetch only if the immutable source object is not already available locally.
