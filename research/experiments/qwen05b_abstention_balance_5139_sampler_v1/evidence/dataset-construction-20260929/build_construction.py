from __future__ import annotations
import hashlib, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from make_dataset import build

FORMAL_SENTINEL = 903520260929
SUPPORT_SENTINEL = 903520260930
ALLOCATION = "qwen5139-dataset-construction-20260929"

data = build(FORMAL_SENTINEL, SUPPORT_SENTINEL, ALLOCATION)
raw = (json.dumps(data, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
Path("dataset.json").write_bytes(raw)
print(json.dumps({
    "run_kind": "construction-only",
    "allocation": ALLOCATION,
    "formal_seed_sentinel": FORMAL_SENTINEL,
    "support_seed_sentinel": SUPPORT_SENTINEL,
    "bytes": len(raw),
    "sha256": hashlib.sha256(raw).hexdigest(),
    "support_pool": len(data["support_pool"]),
    "heldout_pool": len(data["heldout_pool"]),
    "heldout": len(data["heldout"]),
    "support_counts": data["support_counts"],
}, sort_keys=True))

