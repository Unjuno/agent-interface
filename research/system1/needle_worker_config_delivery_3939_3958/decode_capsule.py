"""Byte-bound reconstruction of retained artifacts; NEVER invokes training/workers.

Numeric fixture/logit arrays are encoded as recipes and checked against ORIGINAL
file hashes. This is not a platform-independent verbatim archive. Exact PyTorch
2.10.0 CPU numerical compatibility is required; any mismatch stops decoding.
The original full tar.xz archives remain the canonical verbatim byte copies.
"""
import argparse
import base64
import hashlib
import json
import lzma
from pathlib import Path, PurePosixPath

SEEDS = {3912101, 3912102, 3912201, 3912202, 3912203}
MAX_CAPSULE = 2_000_000
MAX_FILES = 300

def sha(data):
    return hashlib.sha256(data).hexdigest()

def canonical(obj, newline=False):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), allow_nan=False).encode() + (b"\n" if newline else b"")

def unpack(capsule_path):
    envelope = json.loads(capsule_path.read_text())
    if envelope["schema"] != "lzma-base64-capsule.v1":
        raise ValueError("capsule_schema")
    if "payload_base64" in envelope:
        encoded = envelope["payload_base64"]
    else:
        encoded = "".join((capsule_path.parent / name).read_text().strip()
                          for name in envelope["payload_parts"])
    raw = base64.b64decode(encoded, validate=True)
    if sha(raw) != envelope["compressed_sha256"]:
        raise ValueError("compressed_digest")
    dec = lzma.LZMADecompressor()
    data = dec.decompress(raw, max_length=MAX_CAPSULE + 1)
    if len(data) > MAX_CAPSULE or not dec.eof or dec.unused_data:
        raise ValueError("capsule_size_or_trailing")
    if len(data) != envelope["uncompressed_size"] or sha(data) != envelope["uncompressed_sha256"]:
        raise ValueError("uncompressed_digest")
    obj = json.loads(data)
    if obj["schema"] != "byte-bound-worker-config-capsule.v1" or len(obj["files"]) > MAX_FILES:
        raise ValueError("inner_schema")
    return obj

def safe_relative(name):
    p = PurePosixPath(name)
    if p.is_absolute() or ".." in p.parts or not p.parts or str(p) != name:
        raise ValueError("unsafe_member_path")
    return Path(*p.parts)

def fixture(torch, seed):
    if type(seed) is not int or seed not in SEEDS:
        raise ValueError("seed_not_allocated")
    def data(n, offset):
        return torch.randn(n, 8, generator=torch.Generator(device="cpu").manual_seed(seed + offset))
    def labels(x, flip=False):
        a, b = (x[:, 0] > 0).long(), (x[:, 1] > 0).long()
        if flip:
            a = 1 - a
        return (a * 2 + b).tolist()
    xa, xb, xe = data(512, 1), data(16, 2), data(4096, 4)
    order = torch.randperm(16, generator=torch.Generator(device="cpu").manual_seed(seed + 20)).tolist()
    rng = torch.Generator(device="cpu").manual_seed(seed + 21)
    seen, schedule = [], []
    for row in order:
        seen.append(row)
        batches = []
        for _ in range(8):
            ix = torch.randint(len(seen), (32,), generator=rng).tolist()
            batches.append([seen[j] for j in ix])
        schedule.append({"row": row, "seen": list(seen), "batches": batches})
    obj = {"base_x": xa.tolist(), "base_y": labels(xa), "support_x": xb.tolist(),
           "support_y": labels(xb, True), "heldout_x": xe.tolist(), "heldout_y": labels(xe, True),
           "order": order, "schedule": schedule, "base_updates": 400}
    return obj, xe

def heldout(torch, state, x, expected):
    # Forward decoding of frozen tensors only: no optimizer, worker or model service.
    base, adapter = state["base"], state["adapter"]
    tensor = lambda obj: torch.tensor(obj, dtype=torch.float32)
    with torch.no_grad():
        h = torch.tanh(torch.nn.functional.linear(x, tensor(base["enc.0.weight"]), tensor(base["enc.0.bias"])))
        logits = torch.nn.functional.linear(h, tensor(base["head.weight"]), tensor(base["head.bias"])) + (h @ tensor(adapter["a"]) @ tensor(adapter["b"])) / 2
    return {"expected": expected, "logits": logits.tolist(), "predictions": logits.argmax(-1).tolist()}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("capsule", type=Path)
    ap.add_argument("output", type=Path)
    args = ap.parse_args()
    payload = unpack(args.capsule)
    args.output.mkdir(parents=True, exist_ok=False)
    files = payload["files"]
    for name in files:
        safe_relative(name)
    count, byte_count = 0, 0
    def emit(name, data):
        nonlocal count, byte_count
        entry = files[name]
        if len(data) != entry["size"] or sha(data) != entry["sha256"]:
            raise ValueError("ORIGINAL_BYTE_HASH_MISMATCH:" + name)
        path = args.output / safe_relative(name)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("xb") as handle:
            handle.write(data)
        count += 1
        byte_count += len(data)
    try:
        for name, entry in sorted(files.items()):
            if entry["kind"] == "literal":
                emit(name, payload["blobs"][entry["blob"]].encode("utf-8"))
        import torch
        if torch.__version__ != payload["torch"]:
            raise ValueError("EXACT_TORCH_VERSION_REQUIRED")
        torch.set_num_threads(1)
        torch.use_deterministic_algorithms(True)
        fixtures, logits_cache = {}, {}
        for name, entry in sorted(files.items()):
            if entry["kind"] == "fixture":
                seed = entry["seed"]
                if seed not in fixtures:
                    fixtures[seed] = fixture(torch, seed)
                emit(name, canonical(fixtures[seed][0], newline=True))
        for name, entry in sorted(files.items()):
            if entry["kind"] == "meta":
                seed = entry["seed"]
                data, x = fixtures[seed]
                state = json.loads((args.output / safe_relative(entry["state"])).read_text())
                key = (seed, state["content_sha256"])
                if key not in logits_cache:
                    logits_cache[key] = heldout(torch, state, x, data["heldout_y"])
                obj = dict(entry["metadata"], heldout=logits_cache[key])
                emit(name, canonical(obj, entry["newline"]))
        if count != len(files):
            raise ValueError("unrecognized_recipe_or_missing_member")
        receipt = {"verdict": "PASS_ORIGINAL_BYTES_RECONSTRUCTED", "files": count,
                   "bytes": byte_count, "torch": torch.__version__,
                   "fixture_generations": len(fixtures), "forward_decodes": len(logits_cache),
                   "optimizer_updates": 0, "worker_invocations": 0, "formal_reruns": 0,
                   "capsule_sha256": sha(args.capsule.read_bytes()),
                   "notice": "Byte-bound decoding, NOT new scientific evidence or a portable verbatim archive."}
        (args.output / "DECODE_RECEIPT.json").write_text(json.dumps(receipt, sort_keys=True, indent=2) + "\n")
        print(json.dumps(receipt, sort_keys=True))
    except BaseException as exc:
        (args.output / "DECODE_STOP.json").write_text(json.dumps({"error": repr(exc), "verified_files": count}, sort_keys=True) + "\n")
        raise

if __name__ == "__main__":
    main()
