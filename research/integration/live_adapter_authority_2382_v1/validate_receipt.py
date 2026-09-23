"""Dependency-free fail-closed validator for authority receipt v1."""
from __future__ import annotations
import re
from typing import Any

HEX40 = re.compile(r"^[0-9a-f]{40}$")
REQUIRED = {"schema","status","scope","owner","provider","fixture","effect_scorer","release","source_identities"}

def validate(receipt: Any) -> tuple[bool, str]:
    if not isinstance(receipt, dict):
        return False, "RECEIPT_NOT_OBJECT"
    if set(receipt) != REQUIRED:
        return False, "RECEIPT_FIELDS_MISMATCH"
    if receipt["schema"] != "agent-interface/live-adapter-authority-receipt-v1":
        return False, "SCHEMA_MISMATCH"
    if receipt["status"] != "DECLARED":
        return False, "AUTHORITY_NOT_DECLARED"
    if not isinstance(receipt["scope"], str) or not receipt["scope"]:
        return False, "SCOPE_MISSING"
    owner = receipt["owner"]
    if not _object(owner, {"principal","purpose"}) or not all(_text(owner[k]) for k in owner):
        return False, "OWNER_INVALID"
    provider = receipt["provider"]
    if not _object(provider, {"name","model","effort"}) or not all(_text(provider[k]) for k in provider):
        return False, "PROVIDER_INVALID"
    fixture = receipt["fixture"]
    if not _object(fixture, {"kind","disposable","display_scope"}) or fixture["kind"] != "linux-x11-chromium" or fixture["disposable"] is not True or not _text(fixture["display_scope"]):
        return False, "FIXTURE_INVALID"
    scorer = receipt["effect_scorer"]
    if not _object(scorer, {"independent","retention"}) or scorer["independent"] is not True or not _text(scorer["retention"]):
        return False, "EFFECT_SCORER_INVALID"
    release = receipt["release"]
    if not _object(release, {"owner","verified"}) or not _text(release["owner"]) or type(release["verified"]) is not bool:
        return False, "RELEASE_INVALID"
    source = receipt["source_identities"]
    if not _object(source, {"preflight_commit","preflight_status"}) or not HEX40.fullmatch(source["preflight_commit"]) or source["preflight_status"] != "PASS_PRECHECK_HOLD_NO_MODEL_AUTHORITY":
        return False, "SOURCE_IDENTITY_INVALID"
    return True, "DECLARED_VALID"

def _object(value: Any, keys: set[str]) -> bool:
    return isinstance(value, dict) and set(value) == keys

def _text(value: Any) -> bool:
    return isinstance(value, str) and bool(value)
