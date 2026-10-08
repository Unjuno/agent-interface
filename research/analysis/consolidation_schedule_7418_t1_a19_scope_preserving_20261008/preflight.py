"""Read-only model-tag and existing Ollama store preflight; never pulls or loads a model."""
import argparse
import hashlib
import json
import re
import urllib.request
from pathlib import Path

MODEL = "qwen3:14b"
EXPECTED = "bdbd181c33f2ed1b31c972991882db3cf4d192569092138a7d29e973cd9debe8"


def check_tag(tag_payload):
    matches = [model for model in tag_payload.get("models", []) if model.get("name") == MODEL]
    if len(matches) != 1:
        raise RuntimeError("expected exactly one local Qwen3 14B tag")
    model = matches[0]
    if model.get("digest") != EXPECTED:
        raise RuntimeError("local model tag digest does not match the frozen digest")
    return {"name": model["name"], "digest": model["digest"], "size": model.get("size")}


def check_store(model_root):
    root = Path(model_root)
    manifest = root/"manifests/registry.ollama.ai/library/qwen3/14b"
    if not manifest.is_file():
        raise RuntimeError("local Qwen3 14B manifest is missing")
    manifest_bytes = manifest.read_bytes()
    document = json.loads(manifest_bytes)
    layers = document.get("layers")
    if not isinstance(layers, list) or not layers:
        raise RuntimeError("model manifest has no layers")
    checked = []
    for layer in layers:
        digest = layer.get("digest", "")
        size = layer.get("size")
        match = re.fullmatch(r"sha256:([0-9a-f]{64})", digest)
        if not match or not isinstance(size, int) or size < 0:
            raise RuntimeError("model manifest contains an invalid layer descriptor")
        blob = root/"blobs"/f"sha256-{match.group(1)}"
        if not blob.is_file() or blob.stat().st_size != size:
            raise RuntimeError(f"manifest blob absent or wrong size: {blob.name}")
        checked.append({"digest": digest, "size": size, "present_size_matched": True})
    return {"manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(), "checked_layers": checked,
            "all_manifest_blobs_present_and_size_matched": True}


def fetch_tags(base_url):
    with urllib.request.urlopen(base_url.rstrip("/")+"/api/tags", timeout=10) as response:
        return json.loads(response.read())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:11435")
    parser.add_argument("--model-root", required=True)
    args = parser.parse_args()
    report = {"model": check_tag(fetch_tags(args.base_url)), "store": check_store(args.model_root),
              "pull_performed": False, "inference_performed": False}
    print(json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
