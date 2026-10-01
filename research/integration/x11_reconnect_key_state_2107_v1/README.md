# Retained reconnect key-state evidence

Evidence-only delivery for Issue #4135. No shared runtime source is modified.

- `REPORT.md`: result and H/T/D/C/U.
- `FREEZE.json`: original 12-case-batch freeze, before v1 formal.
- `FREEZE_V2.json`: fresh allocation freeze after v1 STOP; scientific source hashes unchanged, batch serialization only changed.
- `AUDIT.json`, `CONTROLS.json`, `POSTFORMAL.json`: v2 retained verification summaries.
- readable source files: exact candidate/observer/app/audit/control sources used by v2; `run_case.py` and the complete frozen source set are retained in the archive.
- `EVIDENCE.part00.b64` … `EVIDENCE.part04.b64` + `EVIDENCE_BASE64.json`: lossless Base64 transport of the 36,032-byte XZ/TAR archive containing 324 source/construction/v1-STOP/v2-raw files.
- `restore_b64.py`: bounded read-only restoration. It verifies every part and the full archive SHA-256 before extracting only ordinary files into an absent destination.

Read-only reconstruction:

```sh
python -B restore_b64.py /tmp/reconnect-4135-review
python -B /tmp/reconnect-4135-review/study/audit.py /tmp/reconnect-4135-review/formal_v2
python -B /tmp/reconnect-4135-review/study/controls.py /tmp/reconnect-4135-review/formal_v2
python -B -m unittest -v /tmp/reconnect-4135-review/study/test_policy.py
```

Do **not** run the consumed `run_case.py` or either formal allocation.
