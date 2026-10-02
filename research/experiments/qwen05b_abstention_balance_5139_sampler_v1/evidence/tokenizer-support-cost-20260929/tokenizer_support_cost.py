"""Offline, tokenizer-only support-prompt length characterization for #5139."""
from __future__ import annotations

import argparse
import hashlib
import json
import statistics
from collections import defaultdict
from pathlib import Path
import sys

PACKAGE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PACKAGE))
from make_dataset import build  # noqa: E402
from audit_sampler import audit_support_selection  # noqa: E402
from tokenizers import Tokenizer  # noqa: E402

# Full SHA-256 values from the published #5139 local-asset manifest.
EXPECTED = {
    "tokenizer.json": "c0382117ea329cdf097041132f6d735924b697924d6f6fc3945713e96ce87539",
    "tokenizer_config.json": "5b5d4f65d0acd3b2d56a35b56d374a36cbc1c8fa5cf3b3febbbfabf22f359583",
    "vocab.json": "ca10d7e9fb3ed18575dd1e277a2579c16d108e32f27439684afa0e10b1440910",
    "merges.txt": "599bab54075088774b1733fde865d5bd747cbcc7a547c5bc12610e874e26f5e3",
}
DATASET_SHA256 = "d96c4072db2ee3bb1af7503a8ae98e062794072385a15099f32121a7a8caad4b"
FORMAL_SENTINEL = 903520260929
SUPPORT_SENTINEL = 903520260930
ALLOCATION = "qwen5139-dataset-construction-20260929"

parser = argparse.ArgumentParser()
parser.add_argument("--snapshot", required=True, help="Local immutable HF snapshot directory; no network access is used")
args = parser.parse_args()
snapshot = Path(args.snapshot).resolve(strict=True)
actual_hashes = {}
for name, expected in EXPECTED.items():
    path = snapshot / name
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    actual_hashes[name] = digest
    if digest != expected:
        raise SystemExit(f"STOP_TOKENIZER_ASSET_HASH_MISMATCH:{name}:{digest}")

tokenizer = Tokenizer.from_file(str(snapshot / "tokenizer.json"))
dataset = build(FORMAL_SENTINEL, SUPPORT_SENTINEL, ALLOCATION)
canonical_dataset = (json.dumps(dataset, sort_keys=True, separators=(",", ":")) + "\n").encode()
dataset_hash = hashlib.sha256(canonical_dataset).hexdigest()
if dataset_hash != DATASET_SHA256:
    raise SystemExit(f"STOP_CONSTRUCTION_DATASET_HASH_MISMATCH:{dataset_hash}")
if audit_support_selection(dataset):
    raise SystemExit("STOP_INDEPENDENT_SUPPORT_AUDIT")

arms = {}
for arm_name in ("imbalanced", "balanced"):
    rows = dataset["supports"][arm_name]
    prompt_lengths = []
    target_lengths = []
    total_lengths = []
    roundtrip = 0
    by_class: dict[str, dict[str, int]] = defaultdict(lambda: {"rows": 0, "prompt_tokens": 0, "target_tokens": 0})
    for row in rows:
        prompt = row["prompt"]
        target = row["target"]
        prompt_ids = tokenizer.encode(prompt, add_special_tokens=False).ids
        target_ids = tokenizer.encode(target, add_special_tokens=False).ids
        if tokenizer.decode(prompt_ids, skip_special_tokens=False) == prompt:
            roundtrip += 1
        prompt_lengths.append(len(prompt_ids))
        target_lengths.append(len(target_ids))
        total_lengths.append(len(prompt_ids) + len(target_ids))
        record = by_class[row["class"]]
        record["rows"] += 1
        record["prompt_tokens"] += len(prompt_ids)
        record["target_tokens"] += len(target_ids)
    arms[arm_name] = {
        "rows": len(rows),
        "prompt_tokens_total": sum(prompt_lengths),
        "target_tokens_total": sum(target_lengths),
        "prompt_tokens_min_median_max": [min(prompt_lengths), statistics.median(prompt_lengths), max(prompt_lengths)],
        "target_tokens_min_median_max": [min(target_lengths), statistics.median(target_lengths), max(target_lengths)],
        "raw_prompt_plus_target_max": max(total_lengths),
        "exact_prompt_roundtrips": roundtrip,
        "by_class": dict(sorted(by_class.items())),
    }

imbalanced_total = arms["imbalanced"]["prompt_tokens_total"]
balanced_total = arms["balanced"]["prompt_tokens_total"]
result = {
    "status": "PASS_TOKENIZER_ONLY_SUPPORT_COST_CHARACTERIZATION",
    "tokenizer": {
        "implementation": "tokenizers.Tokenizer.from_file",
        "tokenizers_version": __import__("tokenizers").__version__,
        "snapshot": snapshot.name,
        "assets_sha256": actual_hashes,
        "added_special_tokens": False,
    },
    "dataset": {
        "allocation": ALLOCATION,
        "formal_seed_sentinel": FORMAL_SENTINEL,
        "support_seed_sentinel": SUPPORT_SENTINEL,
        "canonical_sha256": dataset_hash,
        "independent_support_audit_errors": [],
    },
    "arms": arms,
    "balanced_over_imbalanced_prompt_token_ratio": balanced_total / imbalanced_total,
    "scope": "offline tokenizer-only CPU characterization of raw row prompt/target strings; not trainer/chat serialization or a model/GPU result",
}
out = Path(__file__).with_name("result.json")
out.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
print(json.dumps(result, sort_keys=True))
