"""Verify the frozen package after the GitHub text-upload CRLF suffix."""
from __future__ import annotations

import hashlib
import argparse
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_FREEZE_SHA256 = "8d8c337e9258ab7be87f426a6f29d3f4a7a36c0d78de5349d984fafa09b6d94f"
EXPECTED_MANIFEST_SHA256 = "c0f6c8a2f9cfe9711eacbbae9d787c6364e0216dd259be7734b763f4b3140243"


def payload(path: Path, expected_sha256: str, expected_size: int | None = None) -> tuple[bytes, bool]:
    raw = path.read_bytes()
    if (hashlib.sha256(raw).hexdigest() == expected_sha256
            and (expected_size is None or len(raw) == expected_size)):
        return raw, False
    normalized = raw.endswith(b"\r\n")
    candidate = raw[:-2] if normalized else raw
    if hashlib.sha256(candidate).hexdigest() != expected_sha256:
        raise ValueError(f"sha256 mismatch: {path}")
    if expected_size is not None and len(candidate) != expected_size:
        raise ValueError(f"size mismatch: {path}")
    return candidate, normalized


def verify(root: Path = ROOT) -> dict:
    freeze_path = root / "FREEZE.json"
    manifest_path = root / "EVIDENCE_MANIFEST.json"
    freeze_bytes, freeze_suffix = payload(freeze_path, EXPECTED_FREEZE_SHA256)
    manifest_bytes, manifest_suffix = payload(manifest_path, EXPECTED_MANIFEST_SHA256)
    freeze = json.loads(freeze_bytes)
    manifest = json.loads(manifest_bytes)
    sidecar = (root / "FREEZE.sha256").read_bytes()
    if sidecar.endswith(b"\r\n"):
        sidecar = sidecar[:-2]
    if sidecar.decode("ascii").strip().split()[0] != EXPECTED_FREEZE_SHA256:
        raise ValueError("FREEZE.sha256 does not bind the frozen FREEZE.json")
    checked = 0
    suffixes = int(freeze_suffix) + int(manifest_suffix)
    for relative, expected in freeze["source_sha256"].items():
        _, had_suffix = payload(root / relative, expected)
        suffixes += int(had_suffix)
        checked += 1
    for entry in manifest["files"]:
        _, had_suffix = payload(root / entry["repository_path"], entry["sha256"], entry["size_bytes"])
        suffixes += int(had_suffix)
        checked += 1
    return {"schema": "visual-encoding-570-publication-transport-verification-v1",
            "decision": "PASS_TRANSPORT_SUFFIX_ONLY", "payloads_verified": checked,
            "payloads_with_one_terminal_crlf_removed_for_hashing": suffixes,
            "freeze_sha256": EXPECTED_FREEZE_SHA256,
            "manifest_sha256": EXPECTED_MANIFEST_SHA256,
            "writes_or_mutations": False}


def materialize(root: Path, destination: Path) -> dict:
    """Create a verified runnable copy; never rewrite the checkout/evidence."""
    if destination.exists():
        raise FileExistsError(f"destination already exists: {destination}")
    root, destination = root.resolve(), destination.resolve()
    if destination == root or root in destination.parents:
        raise ValueError("destination must be outside the verified source tree")
    verify(root)
    freeze = json.loads((root / "FREEZE.json").read_bytes().removesuffix(b"\r\n"))
    manifest = json.loads((root / "EVIDENCE_MANIFEST.json").read_bytes().removesuffix(b"\r\n"))
    managed = {"FREEZE.json", "FREEZE.sha256", "EVIDENCE_MANIFEST.json"}
    managed.update(freeze["source_sha256"])
    managed.update(entry["repository_path"] for entry in manifest["files"])
    shutil.copytree(root, destination)
    normalized = 0
    for relative in managed:
        target = destination / relative
        raw = target.read_bytes()
        if raw.endswith(b"\r\n"):
            target.write_bytes(raw[:-2])
            normalized += 1
    verify(destination)
    return {"decision": "PASS_MATERIALIZED_VERIFIED_COPY", "destination": str(destination),
            "payloads_normalized": normalized, "source_tree_mutated": False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--materialize", type=Path)
    args = parser.parse_args()
    report = materialize(args.root, args.materialize) if args.materialize else verify(args.root)
    print(json.dumps(report, indent=2, sort_keys=True))

