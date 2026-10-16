#!/usr/bin/env python3
"""Extract a frozen Python-only source view from a Git tree."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

TREE = "2ce07e058ed6b868ea97799e9a7b65deff21da71"
ROOT = Path(__file__).resolve().parents[3]
PREFIXES = (b"research/live_control/", b"research/doom/")


def included(path):
    if not path.endswith(b".py"):
        return False
    for prefix in PREFIXES:
        if path.startswith(prefix) and b"/" not in path[len(prefix):]:
            return True
    return False


def tree_entries():
    raw = subprocess.check_output(
        ["git", "ls-tree", "-r", "-l", "-z", TREE, "--",
         "research/live_control", "research/doom"], cwd=ROOT)
    entries = []
    for record in raw.split(bytes([0])):
        if not record:
            continue
        meta, path = record.split(b"\t", 1)
        mode, kind, oid, size = meta.split()
        if kind == b"blob" and included(path):
            entries.append({
                "path": path.decode("utf-8"),
                "git_blob": oid.decode("ascii"),
                "bytes": int(size),
            })
    entries.sort(key=lambda row: row["path"])
    return entries


def read_blobs(entries):
    proc = subprocess.Popen(
        ["git", "cat-file", "--batch"], cwd=ROOT,
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    assert proc.stdin is not None and proc.stdout is not None
    for row in entries:
        proc.stdin.write(row["git_blob"].encode("ascii") + b"\n")
        proc.stdin.flush()
        header = proc.stdout.readline().split()
        if len(header) != 3 or header[1] != b"blob":
            raise RuntimeError(f"unexpected git cat-file header for {row['path']}: {header!r}")
        size = int(header[2])
        chunks = []
        remaining = size
        while remaining:
            chunk = proc.stdout.read(min(1024 * 1024, remaining))
            if not chunk:
                raise RuntimeError(f"truncated blob for {row['path']}")
            chunks.append(chunk)
            remaining -= len(chunk)
        data = b"".join(chunks)
        if proc.stdout.read(1) != b"\n":
            raise RuntimeError(f"missing blob separator for {row['path']}")
        row["sha256"] = hashlib.sha256(data).hexdigest()
        row["_data"] = data
    proc.stdin.close()
    stderr = proc.stderr.read() if proc.stderr is not None else b""
    code = proc.wait()
    if code:
        raise RuntimeError(f"git cat-file exited {code}: {stderr.decode(errors='replace')}")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest-only", action="store_true")
    ap.add_argument("--manifest", type=Path, required=True)
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()
    entries = tree_entries()
    read_blobs(entries)
    body = {
        "schema": "v15-cleanup-crosspython-source-manifest-v1",
        "git_tree": TREE,
        "file_count": len(entries),
        "total_bytes": sum(row["bytes"] for row in entries),
        "files": [{k: v for k, v in row.items() if k != "_data"}
                  for row in entries],
    }
    encoded = (json.dumps(body, indent=2, ensure_ascii=False) + "\n").encode()
    if args.manifest_only:
        if args.manifest.exists():
            raise FileExistsError(args.manifest)
        args.manifest.parent.mkdir(parents=True, exist_ok=True)
        args.manifest.write_bytes(encoded)
    else:
        if args.out is None:
            ap.error("--out is required unless --manifest-only is used")
        frozen = json.loads(args.manifest.read_text(encoding="utf-8"))
        if frozen != body:
            raise RuntimeError("materialized Git tree differs from committed frozen manifest")
        if args.out.exists():
            raise FileExistsError(args.out)
        for row in entries:
            dest = args.out / row["path"]
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(row["_data"])
    print(json.dumps({
        "result": "SOURCE_FREEZE_READY" if args.manifest_only else "SOURCE_TREE_MATERIALIZED",
        "tree": TREE, "files": len(entries), "bytes": body["total_bytes"],
        "manifest": str(args.manifest),
        "output": None if args.manifest_only else str(args.out),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
