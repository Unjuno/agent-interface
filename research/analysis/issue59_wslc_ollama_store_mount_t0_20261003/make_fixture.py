#!/usr/bin/env python3
"""Freeze manifest identity and blob metadata from the existing Ollama store."""
import argparse
import hashlib
import json
import re
import stat
from pathlib import Path

EXPECTED = {
    "qwen2.5:3b": "manifests/registry.ollama.ai/library/qwen2.5/3b",
    "qwen2.5vl:3b": "manifests/registry.ollama.ai/library/qwen2.5vl/3b",
    "qwen3:4b": "manifests/registry.ollama.ai/library/qwen3/4b",
}
DIGEST_RE = re.compile(r"^sha256:([0-9a-f]{64})$")


def build(root: Path):
    models = []
    for name, manifest_rel in EXPECTED.items():
        manifest_path = root / manifest_rel
        if not manifest_path.is_file() or manifest_path.is_symlink():
            raise RuntimeError("manifest missing or not regular: " + name)
        manifest_bytes = manifest_path.read_bytes()
        doc = json.loads(manifest_bytes)
        descriptors = [doc.get("config", {}), *doc.get("layers", [])]
        blobs = []
        for descriptor in descriptors:
            digest = descriptor.get("digest", "")
            match = DIGEST_RE.fullmatch(digest)
            if not match:
                raise RuntimeError("invalid descriptor digest: " + name)
            rel = "blobs/sha256-" + match.group(1)
            path = root / rel
            if not path.is_file() or path.is_symlink():
                raise RuntimeError("blob missing or not regular: " + name + ":" + digest)
            size = path.stat().st_size
            if size != descriptor.get("size"):
                raise RuntimeError("declared blob size mismatch: " + name + ":" + digest)
            blobs.append({"digest": digest, "path": rel, "size": size})
        models.append({"name": name, "manifest_rel": manifest_rel,
                       "manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
                       "schema_version": doc.get("schemaVersion"),
                       "media_type": doc.get("mediaType"), "blobs": blobs})
    return {"schema_version": 1, "store_label": "existing Windows Ollama model store",
            "models": models}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("store", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    result = build(args.store)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"models": len(result["models"]),
                      "manifest_layers_and_config": sum(len(m["blobs"]) for m in result["models"])}))


if __name__ == "__main__":
    main()
