"""Export only the370 pinned inert inputs from Git, without running them."""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path


def demand(condition, message):
    if not condition:
        raise ValueError(message)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("repository", type=Path)
    parser.add_argument("destination", type=Path)
    parser.add_argument("--prefetch", action="store_true", help="fetch only the selected object IDs in one request")
    args = parser.parse_args()
    package = Path(__file__).resolve().parent
    data = (package / "INPUTS.json").read_bytes()
    freeze = json.loads((package / "FREEZE.json").read_bytes())
    demand(hashlib.sha256(data).hexdigest() == freeze["input_manifest_sha256"], "manifest-binding")
    manifest = json.loads(data)
    source = manifest["source_commit"]
    demand(source == "332da58a9b6b825c384a142dfb59d7ed2b8b774e", "source")
    files = manifest["files"]
    demand(len(files) == 370 and not args.destination.exists(), "count-or-existing-destination")
    prefixes = ["research/analysis/observation_intervention_6526_a02_orbstack_20261003/",
                "research/analysis/observation_intervention_6526_a03_deadline_audit_only_20261003/"]
    inventory = subprocess.run(["git", "ls-tree", "-r", source, "--", *prefixes],
                               cwd=args.repository, capture_output=True, check=True)
    tree = {}
    for line in inventory.stdout.decode().splitlines():
        meta, path = line.split("\t")
        tree[path] = meta.split()
    for file in files:
        path = file["path"]
        demand(path.startswith(tuple(prefixes)) and ".." not in Path(path).parts and not Path(path).is_absolute(), "path")
        demand(tree.get(path) == ["100644", "blob", file["git_blob"]], "source-tree-binding")
    if args.prefetch:
        wants = ("\n".join(sorted({f["git_blob"] for f in files})) + "\n").encode()
        subprocess.run(["git", "-c", "fetch.negotiationAlgorithm=noop", "fetch", "origin", "--no-tags",
                        "--no-write-fetch-head", "--recurse-submodules=no", "--filter=blob:none", "--stdin"],
                       input=wants, cwd=args.repository, check=True)
    blobs = subprocess.run(["git", "cat-file", "--batch"], cwd=args.repository,
                           input=("\n".join(f["git_blob"] for f in files) + "\n").encode(),
                           capture_output=True, check=True).stdout
    demand(len(blobs) <= 15 * 1024 * 1024, "export-byte-bound")
    offset, parsed = 0, []
    for file in files:
        boundary = blobs.index(b"\n", offset)
        header = blobs[offset:boundary].decode().split()
        demand(header == [file["git_blob"], "blob", str(file["bytes"])], "batch-header")
        offset = boundary + 1
        content = blobs[offset:offset + file["bytes"]]
        offset += file["bytes"] + 1
        demand(hashlib.sha256(content).hexdigest() == file["sha256"], "input-sha256")
        parsed.append((file["path"], content))
    demand(offset == len(blobs), "batch-trailing-bytes")
    args.destination.mkdir(parents=True, exist_ok=False)
    for path, content in parsed:
        destination = args.destination / path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(content)
    print(json.dumps({"exported": len(parsed), "bytes": sum(len(c) for _, c in parsed), "source_commit": source}))


if __name__ == "__main__":
    main()
