"""Construction-only package rules for the #5073 OrbStack experiment."""
from __future__ import annotations

import hashlib
import json
from typing import Any

OLD = 3788
NEW = 3789
SEED_SHA256 = "2e7bff5a2c6ffd35935c5e3c88d08cb686fb736d332c8d5cdb24bb1b67dc873a"
IMAGE_ID = "sha256:392307d22300de8b5986851a12d9176dfc0fc073e65bf6523ebd7dcbeb23564e"
PHASES = (
    "phase_1", "phase_2", "phase_3", "phase_4", "phase_5", "phase_6", "phase_7",
)
UNSAFE_PHASES = (
    "phase_1", "phase_2", "phase_3", "phase_4", "phase_5", "phase_6", "phase_7",
)


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def digest(package: dict[str, Any]) -> str:
    body = {key: value for key, value in package.items() if key != "payload_sha256"}
    return hashlib.sha256(canonical_bytes(body)).hexdigest()


def valid(package: Any) -> bool:
    return isinstance(package, dict) and isinstance(package.get("generation"), int) and package.get("payload_sha256") == digest(package)


def successor(seed: dict[str, Any]) -> dict[str, Any]:
    import copy
    result = copy.deepcopy(seed)
    result["generation"] = NEW
    result["provenance"] = dict(result["provenance"])
    result["provenance"]["allocation"] = "needle-publication-orbstack-bind-5066-20260928-01"
    result["provenance"]["predecessor_issue"] = 3890
    result["payload_sha256"] = digest(result)
    return result
