# Lossless raw call bundles

`results/construction/raw_calls.jsonl.gz` and `results/formal/raw_calls.jsonl.gz` are each stored as numbered `.partNNN` byte chunks because of GitHub MCP payload limits. Concatenate each set in ascending filename order to reconstruct the exact gzip stream; `EVIDENCE_MANIFEST.json` binds every part, the reconstructed gzip bytes, and the original uncompressed JSONL bytes by SHA-256.

Example with Python (from this directory):

```python
from pathlib import Path
for split in ("construction", "formal"):
    parts = sorted(Path(f"results/{split}").glob("raw_calls.jsonl.gz.part*"))
    Path(f"results/{split}/raw_calls.jsonl.gz").write_bytes(b"".join(p.read_bytes() for p in parts))
```

Use `gzip -d` or Python `gzip.decompress` after reconstruction.
