# X11 resync snapshot-cut evidence — Issue #4318

This directory losslessly publishes the already completed `rsq2-4318-20260924-01` allocation from the abandoned source branch `research/x11-resync-cut-677-20260924-rsq2`. The source/gate freeze preceded seven two-session batches: 14 actual private-X11 sessions and 28 paired reducer observations. Do not rerun those sessions.

## Restore and verify

The package includes 669 evidence files in an XZ archive and 15 frozen source files in a separate archive. `unpack.py` validates each Base64-part hash, archive length and SHA-256, bounded XZ expansion, member count, and safe relative paths; it only writes data into a new destination and does not execute restored source.

```sh
review_dir=$(mktemp -d)
python3 -B unpack.py EVIDENCE_MANIFEST.json "$review_dir/evidence"
python3 -B unpack.py SOURCE_MANIFEST.json "$review_dir/source"
python3 -B "$review_dir/source/source/audit.py" "$review_dir/evidence"
python3 -B "$review_dir/source/source/controls.py" \
  "$review_dir/evidence" formal "$review_dir/controls"
(cd "$review_dir/source/source" && python3 -B -m unittest -v test_policy)
```

Verified locally on 2026-09-28 from the remote branch bytes:

- Evidence archive: 57,264 bytes, SHA-256 `39aa9b7844d4e5b9ca90d10172b54b3ce836bf8319741e9f2e7599aa868de912`; 669/669 files restored.
- Frozen source archive: 13,252 bytes, SHA-256 `0810e7e2b735f06a323a377fb8f7ce36c49fbe401a47a7ed45c21cead89e5774`; 15/15 files restored.
- Raw-only audit exactly matched the saved `AUDIT.json`: `PASS_X11_RESYNC_CUT_SCOPED`, 2,478 checks, `errors=[]`.
- All 12 copied-evidence controls changed the target evidence and were rejected; replay exactly matched saved `CONTROLS.json`.
- Frozen policy unit tests: 7/7 passed.

These are read-only archive/audit/unit checks, not a reproduction of the native-X11 experiment or independent human review. Container-backed replay was unavailable during recovery because the local Docker daemon did not answer `docker info`; no container or new experiment was started. The original report, H/T/D/C/U, construction incidents, raw records, and claim limits are retained inside the evidence archive. This scoped result does not establish automatic resync, arbitrary GUI atomicity, a natural failure rate, action authority, or a production/performance benefit.
