# Retained reconnect key-state evidence

Evidence-only delivery for Issue #4135. No shared runtime source is modified.

- `REPORT.md`: result and H/T/D/C/U.
- `FREEZE.json`: original 12-case-batch freeze, before v1 formal.
- `FREEZE_V2.json`: fresh allocation freeze after v1 STOP; scientific source hashes unchanged, batch serialization only changed.
- `AUDIT.json`, `CONTROLS.json`, `POSTFORMAL.json`: v2 retained verification summaries.
- readable source files: exact scientific sources used by v2.
- `EVIDENCE.part*.bin` + `EVIDENCE_ARCHIVE.json`: lossless source/construction/v1 STOP/v2 raw evidence.
- `restore.py`, `verify_publication.py`: read-only restoration and validation. Do not rerun `run_case.py` or either consumed formal allocation.
