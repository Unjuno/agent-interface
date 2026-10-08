"""Independent oracle/accounting audit; imports scenario data only, not simulator code."""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
POLICIES = ("CONTEXT_POLICY", "LEASE_ONLY", "ATTENUATED_CHAIN", "CONFINED_CHANNEL", "REVOCATION_STRESS")


def oracle(s: dict, p: str) -> tuple[str, str]:
    if p == "CONTEXT_POLICY":
        return ("ADMITTED", "role_and_global_policy") if s["role_ok"] else ("INVALID", "role_denied")
    if p == "LEASE_ONLY":
        if not (s["role_ok"] and s["lease_valid"] and s["task_match"]):
            return "INVALID", "identity_lease_or_task"
        return "ADMITTED", "lease_only"
    if p == "REVOCATION_STRESS" and s["revoked"]:
        return "REVOKED", "live_parent_revocation_epoch"
    requirements = [
        ("signature_valid", "signature"), ("parent_match", "parent_digest"),
        ("resource_match", "resource"), ("operation_allowed", "operation"),
        ("child_subset", "attenuation"), ("recipient_match", "recipient"),
        ("lease_valid", "lease"), ("task_match", "task"),
        ("single_use_unused", "single_use"),
    ]
    for key, why in requirements:
        if s[key] is not True:
            return "INVALID", why
    if p in ("CONFINED_CHANNEL", "REVOCATION_STRESS") and not s["channel_confined"]:
        return "INVALID", "channel_confinement"
    if p == "ATTENUATED_CHAIN" and s["revoked"]:
        return "REVOKED", "revocation_seen"
    if not s["backend_enforces"]:
        return "UNKNOWN_ENFORCEMENT", "backend_is_advisory"
    return "ENFORCED", "all_declared_gates"


def audit(raw: dict, scenarios: list[dict]) -> list[str]:
    errors = []
    expected = {(s["id"], p): s for s in scenarios for p in POLICIES}
    got = {(r.get("scenario"), r.get("policy")): r for r in raw.get("rows", [])}
    if len(raw.get("rows", [])) != len(expected) or set(got) != set(expected):
        errors.append("row_identity_or_count")
    for key, s in expected.items():
        row = got.get(key)
        if not row:
            continue
        status, reason = oracle(s, key[1])
        should = {
            "status": status, "reason": reason, "safe": s["safe"],
            "unauthorized_admission": status in ("ADMITTED", "ENFORCED") and not s["safe"],
            "safe_rejection": status in ("INVALID", "REVOKED") and s["safe"],
            "dispatch_authorized": status == "ENFORCED",
        }
        for field, value in should.items():
            if row.get(field) != value:
                errors.append(f"{key[0]}:{key[1]}:{field}")
    summary = raw.get("summary", {})
    for p in POLICIES:
        rs = [r for r in raw.get("rows", []) if r.get("policy") == p]
        expected_summary = {
            "unauthorized_admissions": sum(r.get("status") in ("ADMITTED", "ENFORCED") and not r.get("safe") for r in rs),
            "safe_rejections": sum(r.get("status") in ("INVALID", "REVOKED") and r.get("safe") for r in rs),
            "unknown_enforcement": sum(r.get("status") == "UNKNOWN_ENFORCEMENT" for r in rs),
            "authorized_dispatches": sum(r.get("status") == "ENFORCED" for r in rs),
        }
        if summary.get(p) != expected_summary:
            errors.append("summary:" + p)
    return errors


def run(path: Path) -> dict:
    scenarios = json.loads((ROOT / "scenarios.json").read_text(encoding="utf-8"))["scenarios"]
    raw = json.loads(path.read_text(encoding="utf-8"))
    errors = audit(raw, scenarios)
    controls = []
    for label, mutate in (
        ("drop_row", lambda x: x["rows"].pop()),
        ("flip_safe_dispatch", lambda x: x["rows"][0].update(dispatch_authorized=not x["rows"][0]["dispatch_authorized"])),
        ("flip_attack_status", lambda x: x["rows"][5].update(status="ENFORCED")),
        ("change_summary", lambda x: x["summary"]["REVOCATION_STRESS"].update(unauthorized_admissions=999)),
    ):
        altered = copy.deepcopy(raw)
        mutate(altered)
        controls.append({"control": label, "rejected": bool(audit(altered, scenarios))})
    return {"audit": "issue_5325_independent_raw_audit_v1", "row_count": len(raw.get("rows", [])),
            "errors": errors, "controls": controls,
            "all_controls_rejected": all(c["rejected"] for c in controls),
            "disposition": "PASS_CONSTRUCTION_ONLY" if not errors and all(c["rejected"] for c in controls) else "FAIL_AUDIT"}


if __name__ == "__main__":
    print(json.dumps(run(Path(sys.argv[1])), sort_keys=True, indent=2))
