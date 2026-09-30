"""Authority-neutral plan-coverage boundary for the frozen #5268 IR."""
from __future__ import annotations

from candidate import validate_ir


def _need(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def validate_coverage(required_ir: dict, proposed_ir: dict,
                      verifier_profiles: dict[str, dict]) -> dict:
    """Check that a proposed plan preserves required rows and feasible deadlines.

    ``required_ir`` is supplied by a deterministic policy; this function does
    not infer action risk or create evidence, authority, or an action verdict.
    Profiles are a bounded caller-supplied snapshot, not a registry.
    """
    validate_ir(required_ir)
    validate_ir(proposed_ir)
    _need(isinstance(verifier_profiles, dict), "verifier profiles must be an object")

    required = {row["check_id"]: row for row in required_ir["checks"]
                if row["criticality"] != "OPTIONAL"}
    proposed = {row["check_id"]: row for row in proposed_ir["checks"]}
    _need(set(required).issubset(proposed), "mandatory coverage omission")
    for check_id, expected in required.items():
        _need(proposed[check_id] == expected,
              f"mandatory check contract changed: {check_id}")
    for check_id, row in proposed.items():
        if check_id not in required:
            _need(row["criticality"] == "OPTIONAL",
                  f"unrequested non-optional check: {check_id}")

    semantic_keys = set()
    for row in proposed_ir["checks"]:
        key = (row["primitive"], row["subject_ref"], row["required_evidence_role"])
        _need(key not in semantic_keys, "duplicate or conflicting semantic check")
        semantic_keys.add(key)
        if row["deadline"] is None:
            continue
        profile = verifier_profiles.get(row["verifier_class"])
        _need(isinstance(profile, dict), "deadline verifier profile missing")
        bound = profile.get("upper_bound_ms")
        _need(type(bound) is int and bound >= 0, "invalid verifier deadline profile")
        _need(bound <= row["deadline"], "verifier deadline infeasible")

    return {
        "schema": "verification_plan_coverage.v0.1",
        "status": "PLAN_COMPLETE",
        "mandatory_count": len(required),
        "proposed_count": len(proposed),
    }
