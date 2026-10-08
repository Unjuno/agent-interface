# Partial-order replay finite study (#4889)

Start with [REPORT.md](REPORT.md) for the result and its HOLD disposition. The original plan, candidate, and independent raw-only auditor are retained in this directory.

`evidence/RAW.jsonl` is losslessly retained as an archive because the raw JSONL is 3,241,590 bytes. Reconstruct it by concatenating the listed base64 parts in `RAW_ARCHIVE_MANIFEST.json`, decoding to `RAW.jsonl.zip`, verifying the archive SHA-256, extracting `RAW.jsonl`, then verifying the raw SHA-256. `RESULT.json`, `NEGATIVE_CONTROL.json`, `AUDIT.json`, and `CONTROLS.json` are also directly readable under `evidence/`.

The audit-control HOLD is intentional: one frozen corruption mutation was a no-op. Do not repair or rerun this consumed allocation; preserve the first result and audit.
