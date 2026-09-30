import base64, gzip
from pathlib import Path
root=Path(__file__).resolve().parent
packed=base64.b64decode((root/"construction_sentinel_1.json.gz.base64").read_text(encoding="ascii"))
raw=gzip.decompress(packed)
(root/"construction_sentinel_1.json").write_bytes(raw)
print(f"restored_bytes={len(raw)}")
