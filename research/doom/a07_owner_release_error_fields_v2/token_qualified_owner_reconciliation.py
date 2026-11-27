"""Apply token ownership gate to retained owner-release reconciliation."""
import importlib.util
from pathlib import Path

_legacy_path = Path(__file__).with_name("audit_a07_owner_release_reconciliation.py")
_legacy_spec = importlib.util.spec_from_file_location("a07_owner_legacy", _legacy_path)
_legacy = importlib.util.module_from_spec(_legacy_spec)
_legacy_spec.loader.exec_module(_legacy)
legacy_audit = _legacy.audit

_PRECHECK = Path(__file__).resolve().parent.parent / "map01_v39_live_threat_guard_a07_20261009" / "a07_release_token_precheck.py"
_spec = importlib.util.spec_from_file_location("a07_token_precheck", _PRECHECK)
_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_module)

def audit(events, owner_events):
    precheck = _module.token_precheck(events)
    if precheck["status"] != "READY_FOR_FURTHER_CHECKS":
        return {"schema": "a07-token-qualified-owner-reconciliation-v1",
                "status": "HOLD_AMBIGUOUS_TOKEN", "formal_pass": False}
    for cancel in (row for row in events if row.get("event") == "cancel_requested"):
        ident = cancel["id"]
        admissions = [row for row in events if row.get("event") == "input_admission" and row.get("id") == ident]
        if not admissions:
            continue
        cancel_ns = cancel.get("requested_ns")
        if (type(cancel_ns) is not int or any(
                type(row.get("admitted_ns")) is not int or row["admitted_ns"] >= cancel_ns
                for row in admissions)):
            return {"schema": "a07-token-qualified-owner-reconciliation-v1",
                    "status": "HOLD_ADMISSION_ORDER", "formal_pass": False}
        releases = [row for row in events if row.get("event") == "input_released" and row.get("id") == ident]
        if len(releases) != 1:
            return {"schema": "a07-token-qualified-owner-reconciliation-v1",
                    "status": "HOLD_OWNER_RELEASE_IDENTITY", "formal_pass": False}
        owner_release = releases[0].get("owner_release")
        if type(owner_release) is not dict or owner_release.get("intent_token") != admissions[0]["intent_token"]:
            return {"schema": "a07-token-qualified-owner-reconciliation-v1",
                    "status": "HOLD_OWNER_RELEASE_IDENTITY", "formal_pass": False}
    result = legacy_audit(events, owner_events)
    result["schema"] = "a07-token-qualified-owner-reconciliation-v1"
    result["token_ownership_unambiguous"] = True
    return result
