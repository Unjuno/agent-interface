"""Read-only identity check for the isolated Ollama server and model store."""
import argparse
import json
import urllib.request
from pathlib import Path

MODEL = "qwen3:14b"
EXPECTED = "bdbd181c33f2ed1b31c972991882db3cf4d192569092138a7d29e973cd9debe8"


def check(tags, store):
    matches = [m for m in tags.get("models", []) if m.get("name") == MODEL]
    if len(matches) != 1:
        raise RuntimeError(f"expected exactly one {MODEL} tag, found {len(matches)}")
    tag = matches[0]
    if tag.get("digest") != EXPECTED:
        raise RuntimeError("private tag digest differs from frozen digest")
    manifest = Path(store) / "manifests/registry.ollama.ai/library/qwen3/14b"
    if not manifest.is_file():
        raise RuntimeError("private store is missing the tag manifest")
    manifest_data = json.loads(manifest.read_text())
    layers = manifest_data.get("layers", [])
    if not layers or not any(layer.get("digest") == f"sha256:{EXPECTED}" for layer in layers):
        raise RuntimeError("manifest does not reference the frozen model digest")
    checked = []
    for layer in layers:
        digest = layer.get("digest", "")
        if not digest.startswith("sha256:"):
            raise RuntimeError("manifest contains a non-SHA256 layer")
        blob = Path(store) / f"blobs/{digest.replace(':', '-')}"
        if not blob.is_file() or blob.stat().st_size != layer.get("size"):
            raise RuntimeError(f"missing or size-mismatched private blob {digest}")
        checked.append({"digest": digest, "size_bytes": blob.stat().st_size,
                        "media_type": layer.get("mediaType")})
    if not any(x["media_type"] == "application/vnd.ollama.image.model" for x in checked):
        raise RuntimeError("manifest has no model layer")
    return {"model": MODEL, "digest": tag["digest"], "tag_size_bytes": tag.get("size"),
            "manifest": str(manifest), "checked_layers": checked,
            "all_manifest_blobs_present_and_size_matched": True, "api_tag_count": 1}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", default="http://127.0.0.1:11435")
    ap.add_argument("--store", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    with urllib.request.urlopen(args.base_url.rstrip("/") + "/api/tags", timeout=10) as response:
        tags = json.loads(response.read())
    result = check(tags, args.store)
    result["base_url"] = args.base_url
    Path(args.out).write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
