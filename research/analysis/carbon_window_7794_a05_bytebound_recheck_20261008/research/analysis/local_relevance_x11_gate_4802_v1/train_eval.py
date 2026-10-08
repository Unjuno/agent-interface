"""One frozen CPU-only fit/evaluation for Issue #4799."""
import hashlib
import json
import os
import random
import struct
import time
import zlib
from pathlib import Path

import torch
from torch import nn
from torch.nn import functional as F

SEED = 2188
STEPS = 120
THRESHOLD = 0.98
W, H = 320, 240


class TinyGate(nn.Module):
    def __init__(self):
        super().__init__()
        self.features = nn.Sequential(nn.Conv2d(2, 4, 3, padding=1), nn.ReLU(),
                                      nn.Conv2d(4, 4, 3, padding=1), nn.ReLU(),
                                      nn.AdaptiveMaxPool2d(1), nn.Flatten())
        self.head = nn.Linear(4, 2)

    def forward(self, x):
        return self.head(self.features(x))


def digest(b):
    return hashlib.sha256(b).hexdigest()


def load_pair(root, row):
    before = zlib.decompress((root / row["before_file"]).read_bytes())
    after = zlib.decompress((root / row["after_file"]).read_bytes())
    if digest(before) != row["before_sha256"] or digest(after) != row["after_sha256"]:
        raise RuntimeError("SOURCE_PIXEL_HASH_MISMATCH")
    if len(before) != row["raw_bytes_each"] or len(after) != len(before):
        raise RuntimeError("RAW_LENGTH_MISMATCH")
    bpp = row["bits_per_pixel"] // 8
    if bpp != 4 or len(before) != W * H * bpp:
        raise RuntimeError("UNFROZEN_PIXEL_STRIDE")
    changed = torch.tensor([before[i:i+bpp] != after[i:i+bpp]
                            for i in range(0, len(before), bpp)], dtype=torch.float32).view(1, 1, H, W)
    x1, y1, x2, y2 = row["task_roi"]
    mask = torch.zeros((1, 1, H, W), dtype=torch.float32)
    mask[:, :, y1:y2, x1:x2] = 1
    # Exact XGetImage difference and declared task-interest ROI, max pooled without interpolation.
    delta32 = F.adaptive_max_pool2d(changed, (32, 32))
    mask32 = F.adaptive_max_pool2d(mask, (32, 32))
    return torch.cat((delta32, mask32), dim=1)


def main():
    if os.environ.get("CUDA_VISIBLE_DEVICES") != "":
        raise RuntimeError("GPU_NOT_DISABLED")
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    random.seed(SEED)
    torch.manual_seed(SEED)
    root = Path(os.environ["DATA_DIR"])
    out = Path(os.environ["OUT_DIR"])
    out.mkdir(parents=True, exist_ok=False)
    rows = [json.loads(line) for line in (root / "pairs.jsonl").read_text().splitlines() if line]
    if len(rows) != 120 or sum(r["split"] == "train" for r in rows) != 80 or sum(r["split"] == "heldout" for r in rows) != 40:
        raise RuntimeError("FROZEN_DATASET_CARDINALITY_MISMATCH")
    if {r["family"] for r in rows if r["split"] == "train"} != {0, 1, 2, 3} or {r["family"] for r in rows if r["split"] == "heldout"} != {4, 5}:
        raise RuntimeError("FAMILY_SPLIT_LEAKAGE")
    tensors = [(r, load_pair(root, r)) for r in rows]
    train = [(r, x) for r, x in tensors if r["split"] == "train"]
    heldout = [(r, x) for r, x in tensors if r["split"] == "heldout"]
    model = TinyGate().cpu()
    params = sum(p.numel() for p in model.parameters())
    started = time.monotonic()
    optim = torch.optim.Adam(model.parameters(), lr=0.01)
    xs = torch.cat([x for _, x in train])
    ys = torch.tensor([int(r["label_relevant"]) for r, _ in train], dtype=torch.long)
    for _ in range(STEPS):
        optim.zero_grad(set_to_none=True)
        loss = F.cross_entropy(model(xs), ys)
        loss.backward()
        optim.step()
    fit_seconds = time.monotonic() - started
    torch.save({"state_dict": model.state_dict(), "seed": SEED, "steps": STEPS}, out / "model.pt")
    model.eval()
    decisions = []
    with torch.no_grad():
        for row, x in heldout:
            # Critical ROI has unconditional full-forward priority; still record the score for diagnosis.
            probs = model(x).softmax(dim=1)[0]
            predicted_irrelevant = float(probs[0])
            suppress = bool(not row["critical"] and predicted_irrelevant >= THRESHOLD)
            decision = "SUPPRESS" if suppress else "FULL_FORWARD"
            decisions.append({"id": row["id"], "family": row["family"], "kind": row["kind"],
                              "label_relevant": row["label_relevant"], "critical": row["critical"],
                              "p_irrelevant": predicted_irrelevant, "threshold": THRESHOLD,
                              "decision": decision, "reason": "critical_override" if row["critical"] else "model_threshold"})
    model_bytes = (out / "model.pt").read_bytes()
    result = {"schema": "issue-4799-fit-eval-v1", "seed": SEED, "optimizer": "Adam(lr=0.01)",
              "steps": STEPS, "loss": "cross_entropy", "device": "cpu", "torch_version": torch.__version__,
              "cuda_available": torch.cuda.is_available(), "threads": torch.get_num_threads(),
              "parameter_count": params, "train_count": len(train), "heldout_count": len(heldout),
              "train_families": [0, 1, 2, 3], "heldout_families": [4, 5],
              "fit_seconds_monotonic": fit_seconds, "threshold": THRESHOLD,
              "model_sha256": digest(model_bytes), "decisions": decisions,
              "missing_source_policy": "YIELD", "stale_source_policy": "YIELD", "ambiguous_policy": "YIELD",
              "critical_policy": "FULL_FORWARD"}
    (out / "result.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(json.dumps({k: v for k, v in result.items() if k != "decisions"}, sort_keys=True))


if __name__ == "__main__":
    main()

