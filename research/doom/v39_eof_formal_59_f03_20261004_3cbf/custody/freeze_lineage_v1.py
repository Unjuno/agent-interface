"""Offline verification of retained F03 freeze manifests and Git source trees."""
from __future__ import annotations

import base64
import hashlib
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
WITNESS = HERE / "freeze-manifests" / "GIT_OBJECT_WITNESS.json"
MANIFESTS = {
    "predecessor": {
        "snapshot": HERE / "freeze-manifests" / "PRELAUNCH_FREEZE-fe2dbe361940.md",
        "commit": "fe2dbe3619403b4b356bc0bd365f548a21030812",
        "manifest_blob": "8a8fab7ec3da0c6b9fac17cff87c50b228b93b87",
        "commit_tree": "868b6ef0d40e73a429e92d5127fbfac05b40c366",
        "source_tree": "5278d4b383a09771abe9b822885f6f04308ee780",
        "source_commit": "b75b65de7561bdf552383e7bbce1ac6064a53595",
        "source_commit_tree": "5278d4b383a09771abe9b822885f6f04308ee780",
    },
    "current_final": {
        "snapshot": HERE / "freeze-manifests" / "PRELAUNCH_FREEZE-43f9a0008bf7.md",
        "commit": "43f9a0008bf75da19865cfdea2898d1b896fbbc3",
        "manifest_blob": "526a5a066d3bcc5f348b5415cfebc3e53eea706a",
        "commit_tree": "2a8c0d1858d237eb0405101e137b39909dff4c5e",
        "source_tree": "338afba37b8c9fe28fe410ec56a5c0788c96e614",
        # The source commit named in the freeze text is not publicly retrievable;
        # the retained Merkle tree and each archived file blob are verified.
        "source_commit": "6d8387caa8a004ebbdadc377e499b85b3b3a10db",
        "source_commit_tree": None,
    },
}
MANIFEST_PATH = "research/doom/v39_eof_formal_59_f03_20261004_3cbf/PRELAUNCH_FREEZE.md"
MEMBER_LINE = re.compile(r"(?m)^([0-9a-f]{64})  (research/[^\n]+)$")
ARCHIVE_LINE = re.compile(r"Exact eight-file archive SHA-256: `([0-9a-f]{64})`")
SOURCE_TREE_LINE = re.compile(r"The frozen input tree is commit `[^`]+` / tree `([0-9a-f]{40})`")


def git_oid(kind: str, data: bytes) -> str:
    return hashlib.sha1(kind.encode("ascii") + b" " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()


def load_objects() -> dict[str, tuple[str, bytes]]:
    payload = json.loads(WITNESS.read_text(encoding="utf-8"))
    if payload.get("schema") != "f03-git-object-witness-v1":
        raise ValueError("unsupported Git object witness")
    objects = {}
    for oid, record in payload.get("objects", {}).items():
        kind = record.get("type")
        data = base64.b64decode(record["data_b64"], validate=True)
        if kind not in ("commit", "tree") or git_oid(kind, data) != oid:
            raise ValueError(f"invalid witnessed Git object {oid}")
        objects[oid] = (kind, data)
    return objects


def commit_tree(oid: str, objects: dict[str, tuple[str, bytes]]) -> str:
    kind, data = objects[oid]
    if kind != "commit":
        raise ValueError(f"{oid} is not a commit")
    match = re.search(rb"(?m)^tree ([0-9a-f]{40})$", data)
    if match is None:
        raise ValueError(f"commit {oid} has no root tree")
    return match.group(1).decode("ascii")


def tree_entries(oid: str, objects: dict[str, tuple[str, bytes]]) -> dict[str, tuple[str, str]]:
    kind, data = objects[oid]
    if kind != "tree":
        raise ValueError(f"{oid} is not a tree")
    entries = {}
    offset = 0
    while offset < len(data):
        space = data.index(b" ", offset)
        nul = data.index(b"\0", space + 1)
        mode = data[offset:space].decode("ascii")
        name = data[space + 1:nul].decode("utf-8")
        child_oid = data[nul + 1:nul + 21].hex()
        if len(data[nul + 1:nul + 21]) != 20:
            raise ValueError(f"truncated tree object {oid}")
        entries[name] = (mode, child_oid)
        offset = nul + 21
    return entries


def resolve(root: str, path: str, objects: dict[str, tuple[str, bytes]]) -> tuple[str, str]:
    current = root
    parts = path.split("/")
    for index, part in enumerate(parts):
        entries = tree_entries(current, objects)
        if part not in entries:
            raise ValueError(f"{path} missing from witnessed source tree {root}")
        mode, child = entries[part]
        if index < len(parts) - 1:
            if mode not in ("040000", "40000"):
                raise ValueError(f"non-tree parent in path {path}")
            current = child
        else:
            return mode, child
    raise AssertionError("unreachable")


def verify_lineage(name: str, member_bytes: dict[str, bytes]) -> dict:
    expected = MANIFESTS[name]
    objects = load_objects()
    raw = expected["snapshot"].read_bytes()
    manifest_blob = git_oid("blob", raw)
    if manifest_blob != expected["manifest_blob"]:
        raise ValueError(f"{name} snapshot does not match its source Git blob")

    root = commit_tree(expected["commit"], objects)
    if root != expected["commit_tree"]:
        raise ValueError(f"{name} manifest commit tree mismatch")
    mode, manifest_oid = resolve(root, MANIFEST_PATH, objects)
    if mode != "100644" or manifest_oid != manifest_blob:
        raise ValueError(f"{name} manifest is not bound to its source commit tree")

    text = raw.decode("utf-8")
    source_trees = SOURCE_TREE_LINE.findall(text)
    archive_hashes = ARCHIVE_LINE.findall(text)
    member_pairs = MEMBER_LINE.findall(text)
    if source_trees != [expected["source_tree"]] or len(archive_hashes) != 1 or len(member_pairs) != 8:
        raise ValueError(f"{name} freeze manifest is malformed or names another source tree")
    declared_members = {path: digest for digest, path in member_pairs}
    if set(member_bytes) != set(declared_members):
        raise ValueError(f"{name} retained archive member paths differ from its manifest")

    source_tree = expected["source_tree"]
    if source_tree not in objects or objects[source_tree][0] != "tree":
        raise ValueError(f"{name} declared source tree is not present in the witness")
    for path, data in member_bytes.items():
        if hashlib.sha256(data).hexdigest() != declared_members[path]:
            raise ValueError(f"{name} member SHA-256 mismatch: {path}")
        mode, source_blob = resolve(source_tree, path, objects)
        if mode != "100644" or source_blob != git_oid("blob", data):
            raise ValueError(f"{name} archived bytes do not match source tree blob: {path}")

    source_commit_tree = expected["source_commit_tree"]
    if source_commit_tree is not None and commit_tree(expected["source_commit"], objects) != source_commit_tree:
        raise ValueError(f"{name} source commit/tree mismatch")
    return {
        "manifest_commit": expected["commit"],
        "manifest_blob": manifest_blob,
        "manifest_tree": root,
        "source_commit": expected["source_commit"],
        "source_commit_object_available": source_commit_tree is not None,
        "source_tree": source_tree,
        "archive_sha256_from_manifest": archive_hashes[0],
        "member_git_blobs_match_source_tree": True,
    }
