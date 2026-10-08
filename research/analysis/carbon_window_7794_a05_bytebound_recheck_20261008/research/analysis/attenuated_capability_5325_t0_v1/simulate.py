"""No-effect finite simulator for Issue #5325 construction testing only."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
POLICIES = ("CONTEXT_POLICY", "LEASE_ONLY", "ATTENUATED_CHAIN", "CONFINED_CHANNEL", "REVOCATION_STRESS")


def evaluate(s: dict, policy: str) -> tuple[str, str]:
    if policy == "CONTEXT_POLICY":
        return ("ADMITTED", "role_and_global_policy") if s["role_ok"] else ("INVALID", "role_denied")
    if policy == "LEASE_ONLY":
        if not s["role_ok"] or not s["lease_valid"] or not s["task_match"]:
            return "INVALID", "identity_lease_or_task"
        return "ADMITTED", "lease_only"

    if policy == "REVOCATION_STRESS" and s["revoked"]:
        return "REVOKED", "live_parent_revocation_epoch"
    checks = (
        ("signature_valid", "signature"), ("parent_match", "parent_digest"),
        ("resource_match", "resource"), ("operation_allowed", "operation"),
        ("child_subset", "attenuation"), ("recipient_match", "recipient"),
        ("lease_valid", "lease"), ("task_match", "task"),
        ("single_use_unused", "single_use"),
    )
    for field, reason in checks:
        if not s[field]:
            return "INVALID", reason
    if policy in ("CONFINED_CHANNEL", "REVOCATION_STRESS") and not s["channel_confined"]:
        return "INVALID", "channel_confinement"
    if policy == "ATTENUATED_CHAIN" and s["revoked"]:
        return "REVOKED", "revocation_seen"
    if not s["backend_enforces"]:
        return "UNKNOWN_ENFORCEMENT", "backend_is_advisory"
    return "ENFORCED", "all_declared_gates"


def run() -> dict:
    data = json.loads((ROOT / "scenarios.json").read_text(encoding="utf-8"))
    rows = []
    for s in data["scenarios"]:
        for p in POLICIES:
            status, reason = evaluate(s, p)
            rows.append({"scenario": s["id"], "policy": p, "safe": s["safe"],
                         "status": status, "reason": reason,
                         "unauthorized_admission": status in ("ADMITTED", "ENFORCED") and not s["safe"],
                         "safe_rejection": status in ("INVALID", "REVOKED") and s["safe"],
                         "dispatch_authorized": status == "ENFORCED"})
    summary = {}
    for p in POLICIES:
        rs = [r for r in rows if r["policy"] == p]
        summary[p] = {
            "unauthorized_admissions": sum(r["unauthorized_admission"] for r in rs),
            "safe_rejections": sum(r["safe_rejection"] for r in rs),
            "unknown_enforcement": sum(r["status"] == "UNKNOWN_ENFORCEMENT" for r in rs),
            "authorized_dispatches": sum(r["dispatch_authorized"] for r in rs),
        }
    return {"schema": "issue-5325-construction-raw-v1", "rows": rows, "summary": summary}


if __name__ == "__main__":
    print(json.dumps(run(), sort_keys=True, indent=2))
