"""Deterministic package construction shared only by the experiment runner."""
from __future__ import annotations

import base64
import copy
import hashlib
import json
from pathlib import Path
from typing import Any

OLD_GENERATION = 3788
ALLOCATION = "needle-cross-process-publication-overlap-5066-v3-20260928-01"
PREDECESSOR_ISSUE = 5066
INPUT_SHA256 = "2e7bff5a2c6ffd35935c5e3c88d08cb686fb736d332c8d5cdb24bb1b67dc873a"


def canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode("utf-8")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git_blob_sha1(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()


def load_seed(root: Path | None = None) -> tuple[bytes, dict[str, Any]]:
    path = (root or Path(__file__).resolve().parent) / "seed_skill.json.b64"
    raw = base64.b64decode(path.read_bytes().strip(), validate=True)
    if sha256(raw) != INPUT_SHA256:
        raise ValueError("frozen seed SHA-256 mismatch")
    package = json.loads(raw)
    if type(package) is not dict or package.get("generation") != OLD_GENERATION:
        raise ValueError("frozen seed schema/generation mismatch")
    return raw, package


def payload_digest(package: dict[str, Any]) -> str:
    body = {key: value for key, value in package.items() if key != "payload_sha256"}
    return sha256(json.dumps(body, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8"))


def package_for_sequence(seed: dict[str, Any], sequence: int) -> bytes:
    if type(sequence) is not int or sequence < 1:
        raise ValueError("positive publication sequence required")
    package = copy.deepcopy(seed)
    package["generation"] = OLD_GENERATION + sequence
    package["provenance"] = dict(package["provenance"])
    package["provenance"].update({
        "allocation": ALLOCATION,
        "predecessor_issue": PREDECESSOR_ISSUE,
        "publication_sequence": sequence,
    })
    package["payload_sha256"] = payload_digest(package)
    return canonical_bytes(package)


def parsed_package(raw: bytes) -> tuple[bool, int | None]:
    try:
        value = json.loads(raw)
        if not isinstance(value, dict) or type(value.get("generation")) is not int:
            return False, None
        return value.get("payload_sha256") == payload_digest(value), value["generation"]
    except (UnicodeDecodeError, json.JSONDecodeError, TypeError, ValueError):
        return False, None
