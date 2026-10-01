"""Precedence-only adapter for the pinned Formal06 auditor; no execution API."""
from research.x11_midprogram_keymap_5236_formal06_20261001.audit import audit as legacy_audit


def audit_gate(raw: dict, wrapper: dict) -> dict:
    """Preserve the old report and give its existing reasons STOP precedence.

    This adds no input validation, authentication, or formal-run eligibility.
    Malformed-input exceptions from the predecessor are deliberately unchanged.
    """
    legacy_result = legacy_audit(raw, wrapper)
    decision = (
        "STOP_PROVENANCE_OR_RUNNER"
        if legacy_result["reasons"]
        else legacy_result["decision"]
    )
    return {"decision": decision, "legacy_result": legacy_result}
