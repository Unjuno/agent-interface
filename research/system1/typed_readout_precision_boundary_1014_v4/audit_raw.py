#!/usr/bin/env python3
"""Read-only raw-only audit; does not load a model or recompute predictions."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from audit_core import corruption_controls, validate_result

CORPUS_SHA = "85b5bee5d5a69dab1ff0d094cdbad70d4cd66fcff505b36667978817ed30a49c"
MODEL_SHA = {
    ".gitattributes": "11ad7efa24975ee4b0c3c3a38ed18737f0658a5f75a0a96787b576a78a023361",
    "config.json": "18e18afcaccafade98daf13a54092927904649e1dd4eba8299ab717d5d94ff45",
    "generation_config.json": "e558847a8b4402616f1273797b015104dc266fe4b520056fca88823ba8f8ebe6",
    "LICENSE": "832dd9e00a68dd83b3c3fb9f5588dad7dcf337a0db50f7d9483f310cd292e92e",
    "merges.txt": "599bab54075088774b1733fde865d5bd747cbcc7a547c5bc12610e874e26f5e3",
    "model.safetensors": "fdf756fa7fcbe7404d5c60e26bff1a0c8b8aa1f72ced49e7dd0210fe288fb7fe",
    "README.md": "b19c806a904db6dc878a0462e70b551f6b7ac78dfbb88c2eb966ca2b9109ae15",
    "tokenizer.json": "c0382117ea329cdf097041132f6d735924b697924d6f6fc3945713e96ce87539",
    "tokenizer_config.json": "5b5d4f65d0acd3b2d56a35b56d374a36cbc1c8fa5cf3b3febbbfabf22f359583",
    "vocab.json": "ca10d7e9fb3ed18575dd1e277a2579c16d108e32f27439684afa0e10b1440910",
}


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--result", type=Path, required=True)
    ap.add_argument("--corpus", type=Path, required=True)
    ap.add_argument("--model", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    if sha(args.corpus) != CORPUS_SHA:
        raise SystemExit("STOP_CORPUS_HASH_MISMATCH")
    for name, expected in MODEL_SHA.items():
        if sha(args.model / name) != expected:
            raise SystemExit(f"STOP_MODEL_ASSET_HASH_MISMATCH:{name}")
    raw = args.result.read_bytes()
    result = json.loads(raw)
    validate_result(result)
    rejected = corruption_controls(result)
    report = {"status": "AUDIT_PASS_RAW_ONLY", "errors": [],
              "result_sha256": hashlib.sha256(raw).hexdigest(),
              "corpus_sha256": sha(args.corpus),
              "weights_sha256": sha(args.model / "model.safetensors"),
              "rows": len(result["rows"]), "corruption_controls_rejected": rejected,
              "modes": result["modes"]}
    args.out.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()

