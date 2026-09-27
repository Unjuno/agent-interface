"""Shared schema rules for Issue #5045 construction tests; not a formal runner."""
from __future__ import annotations

import hashlib
import json
from typing import Any

OLD_GENERATION = 3788
NEW_GENERATION = 3789
EXPECTED_SEED_PACKAGE_SHA256 = "2e7bff5a2c6ffd35935c5e3c88d08cb686fb736d332c8d5cdb24bb1b67dc873a"
FROZEN_IMAGE_ID = "sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9"
READER_COUNT = 4
PHASES = (
    "atomic_before_validation",
    "atomic_candidate_ready_unpublished",
    "atomic_after_publish",
    "invalid_candidate_refused",
    "diagnostic_before_write",
    "diagnostic_partial_write",
    "diagnostic_after_write",
)


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def payload_digest(package: dict[str, Any]) -> str:
    body = {key: value for key, value in package.items() if key != "payload_sha256"}
    return hashlib.sha256(canonical_bytes(body)).hexdigest()


def validate_package(package: dict[str, Any]) -> bool:
    return (
        isinstance(package, dict)
        and isinstance(package.get("generation"), int)
        and package.get("payload_sha256") == payload_digest(package)
    )


def proposal_disposition(proposal_generation: int, active_generation: int) -> str:
    return "ELIGIBLE_PROPOSAL_ONLY" if proposal_generation == active_generation else "YIELD_STALE_GENERATION"


def candidate_from(package: dict[str, Any]) -> dict[str, Any]:
    """Create the frozen inert successor metadata without changing tensor payload."""
    import copy

    candidate = copy.deepcopy(package)
    candidate["generation"] = NEW_GENERATION
    candidate["provenance"] = dict(candidate["provenance"])
    candidate["provenance"]["allocation"] = "needle-cross-process-publication-5045-v1"
    candidate["provenance"]["predecessor_issue"] = 3890
    candidate["payload_sha256"] = payload_digest(candidate)
    return candidate


