# Formal raw capture wrappers

Each `raw_b64/<original-name>.b64` is the base64 encoding of exactly one original binary `.raw` file referenced by `cases.jsonl`. Decode it to the referenced filename under `raw/`; the original byte count (38,400) and SHA-256 are recorded in each capture artifact object. The auditor read the original local binary files, not these wrappers. The wrappers are lossless publication only.

All 24 scheduled capture attempts completed and are included. Container inspect receipts are redacted summaries; full local inspect JSONs are retained in the task workspace.
