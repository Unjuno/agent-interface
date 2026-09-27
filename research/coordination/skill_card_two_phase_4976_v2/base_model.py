from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Any

VALID_EVIDENCE_ROLES = {"CURRENT", "HINT", "ADMISSION_DEPENDENCY", "PLANNER_CONTEXT", "INVALIDATOR", "EFFECT_EVIDENCE"}

@dataclass(frozen=True)
class Skill:
    skill_id: str
    version: str
    semantic_goal: str
    required_capabilities: tuple[str, ...]
    required_resources: tuple[str, ...]
    allowed_surfaces: tuple[str, ...]
    envelope: dict[str, Any]
    evidence_role: str
    requires_revalidation: bool
    universal_fallback: bool
    implementation_ref: str
    provenance: str

    def card(self) -> dict[str, Any]:
        return {
            "skill_id": self.skill_id,
            "version": self.version,
            "semantic_goal": self.semantic_goal,
            "required_resources": list(self.required_resources),
            "evidence_role": self.evidence_role,
            "requires_revalidation": self.requires_revalidation,
            "provenance": self.provenance,
        }

REGISTRY = {
    "touch_track_v1": Skill("touch_track", "1", "track_target", ("touch",), ("touch.contact1",), ("game",), {}, "CURRENT", False, False, "impl://touch-track-v1", "evidence://574-touch"),
    "pointer_track_v2": Skill("pointer_track", "2", "track_target", ("pointer",), ("pointer.motion",), ("game",), {}, "CURRENT", False, False, "impl://pointer-track-v2", "evidence://6-pointer"),
    "mae_guard_v1": Skill("mae_guard", "1", "detect_context_change", (), (), ("game",), {"nuisance": ["low"]}, "CURRENT", False, False, "impl://mae-guard-v1", "evidence://575-scoped"),
    "raw_current_v1": Skill("raw_current", "1", "detect_context_change", (), (), ("game", "desktop", "browser"), {}, "CURRENT", False, True, "impl://raw-current-v1", "evidence://raw-fallback"),
    "cached_route_v1": Skill("cached_route", "1", "resolve_target", ("pointer",), ("pointer.motion",), ("desktop",), {}, "HINT", True, False, "impl://cached-route-v1", "evidence://663-hint"),
    "fresh_resolve_v1": Skill("fresh_resolve", "1", "resolve_target", ("pointer",), ("pointer.motion",), ("desktop",), {}, "CURRENT", False, True, "impl://fresh-resolve-v1", "evidence://current-resolution"),
    "exclusive_drag_v1": Skill("exclusive_drag", "1", "manipulate_target", ("pointer",), ("pointer.motion", "pointer.buttons"), ("desktop",), {}, "CURRENT", False, False, "impl://exclusive-drag-v1", "evidence://drag"),
    "keyboard_adjust_v1": Skill("keyboard_adjust", "1", "manipulate_target", ("keyboard",), ("keyboard",), ("desktop",), {}, "CURRENT", False, True, "impl://keyboard-adjust-v1", "evidence://keyboard"),
    "browser_click_v1": Skill("browser_click", "1", "activate_target", ("pointer",), ("pointer.buttons",), ("browser",), {}, "CURRENT", False, False, "impl://browser-click-v1", "evidence://browser"),
    "desktop_click_v1": Skill("desktop_click", "1", "activate_target", ("pointer",), ("pointer.buttons",), ("desktop",), {}, "CURRENT", False, True, "impl://desktop-click-v1", "evidence://desktop"),
    "legacy_reveal_v1": Skill("reveal", "1", "reveal_target", ("scroll",), ("scroll",), ("desktop",), {"layout": ["legacy"]}, "CURRENT", False, False, "impl://reveal-v1", "evidence://old-envelope"),
    "reveal_v2": Skill("reveal", "2", "reveal_target", ("scroll",), ("scroll",), ("desktop",), {"layout": ["modern"]}, "CURRENT", False, False, "impl://reveal-v2", "evidence://new-envelope"),
    "special_tracker_v1": Skill("special_tracker", "1", "generic_control", ("touch",), ("touch.contact1",), ("game",), {"nuisance": ["low"]}, "CURRENT", False, False, "impl://special-tracker-v1", "evidence://special"),
    "universal_control_v1": Skill("universal_control", "1", "generic_control", (), (), ("game", "desktop", "browser"), {}, "CURRENT", False, True, "impl://universal-control-v1", "evidence://universal"),
}

class DetailLoader:
    def __init__(self):
        self.loaded: list[str] = []
    def load(self, registry_key: str) -> dict[str, str]:
        self.loaded.append(registry_key)
        s = REGISTRY[registry_key]
        return {"implementation_ref": s.implementation_ref, "provenance": s.provenance, "version": s.version}


def hard_check(skill: Skill, context: dict[str, Any]) -> tuple[bool, str, str]:
    if skill.evidence_role not in VALID_EVIDENCE_ROLES:
        return False, "UNKNOWN_EVIDENCE_ROLE", "REJECTED"
    caps = set(context["capabilities"])
    if any(c not in caps for c in skill.required_capabilities):
        return False, "CAPABILITY_UNAVAILABLE", "REJECTED"
    resources = set(context["available_resources"])
    if any(r not in resources for r in skill.required_resources):
        return False, "RESOURCE_UNAVAILABLE", "REJECTED"
    if context["surface"] not in skill.allowed_surfaces:
        return False, "SURFACE_MISMATCH", "REJECTED"
    for key, allowed in skill.envelope.items():
        if context.get(key) not in allowed:
            return False, f"OUT_OF_ENVELOPE:{key}", "REJECTED"
    if skill.evidence_role == "HINT":
        if not skill.requires_revalidation:
            return False, "HINT_WITHOUT_REVALIDATION_CONTRACT", "REJECTED"
        if not context.get("current_revalidation_available", False):
            return False, "REVALIDATION_UNAVAILABLE", "REJECTED"
        return True, "NEEDS_CURRENT_REVALIDATION", "REVALIDATION_REQUIRED"
    if skill.evidence_role != "CURRENT":
        return False, f"ROLE_NOT_EXECUTABLE:{skill.evidence_role}", "REJECTED"
    return True, "APPLICABLE", "FALLBACK" if skill.universal_fallback else "EXECUTABLE"


def explicit_revalidate(registry_key: str, context: dict[str, Any]) -> dict[str, Any]:
    skill = REGISTRY[registry_key]
    assert skill.evidence_role == "HINT" and skill.requires_revalidation
    assert context.get("current_revalidation_available", False)
    return {
        "receipt_id": f"current-revalidation::{registry_key}::{context['case_id']}",
        "source_role": "HINT",
        "output_role": "ADMISSION_DEPENDENCY",
        "freshness": "CURRENT",
        "source_skill_version": skill.version,
        "source_provenance": skill.provenance,
    }


def select_semantic_only(case: dict[str, Any]) -> dict[str, Any]:
    loader = DetailLoader()
    order = sorted(case["scores"], key=lambda k: (-case["scores"][k], k))
    top = order[0]
    detail = loader.load(top)
    skill = REGISTRY[top]
    applicable, reason, candidate_status = hard_check(skill, case["context"])
    return {
        "policy": "SEMANTIC_ONLY",
        "semantic_order": order,
        "filter_log": [],
        "selected_key": top,
        "selected_skill_id": skill.skill_id,
        "selected_version": skill.version,
        "selected_status": "EXPOSED_WITHOUT_HARD_GATE",
        "candidate_hard_applicable": applicable,
        "candidate_hard_reason": reason,
        "candidate_status_if_checked": candidate_status,
        "candidate_card": skill.card(),
        "detail_loaded": loader.loaded,
        "detail": detail,
        "revalidation_receipt": None,
    }


def select_applicability_aware(case: dict[str, Any]) -> dict[str, Any]:
    loader = DetailLoader()
    order = sorted(case["scores"], key=lambda k: (-case["scores"][k], k))
    filter_log = []
    selected = None
    selected_status = None
    reason = None
    for key in order:
        skill = REGISTRY[key]
        ok, why, status = hard_check(skill, case["context"])
        filter_log.append({"key": key, "ok": ok, "reason": why, "status": status})
        if ok:
            selected = key
            selected_status = status
            reason = why
            break
    if selected is None:
        return {
            "policy": "APPLICABILITY_AWARE",
            "semantic_order": order,
            "filter_log": filter_log,
            "selected_key": None,
            "selected_skill_id": None,
            "selected_version": None,
            "selected_status": "ABSTAIN",
            "candidate_hard_reason": "NO_APPLICABLE_SKILL",
            "candidate_card": None,
            "detail_loaded": [],
            "detail": None,
            "revalidation_receipt": None,
        }
    skill = REGISTRY[selected]
    receipt = None
    if selected_status == "REVALIDATION_REQUIRED":
        receipt = explicit_revalidate(selected, case["context"])
        selected_status = "EXECUTABLE_AFTER_REVALIDATION"
    detail = loader.load(selected)
    return {
        "policy": "APPLICABILITY_AWARE",
        "semantic_order": order,
        "filter_log": filter_log,
        "selected_key": selected,
        "selected_skill_id": skill.skill_id,
        "selected_version": skill.version,
        "selected_status": selected_status,
        "candidate_hard_reason": reason,
        "candidate_card": skill.card(),
        "detail_loaded": loader.loaded,
        "detail": detail,
        "revalidation_receipt": receipt,
    }


def validate_registry_entry(raw: dict[str, Any]) -> tuple[bool, str]:
    for field in ("skill_id", "version", "provenance", "evidence_role"):
        if not raw.get(field):
            return False, f"MISSING_{field.upper()}"
    if raw["evidence_role"] not in VALID_EVIDENCE_ROLES:
        return False, "UNKNOWN_EVIDENCE_ROLE"
    if raw.get("mutate_hint_in_place_to_admission"):
        return False, "FORBIDDEN_IN_PLACE_ROLE_PROMOTION"
    return True, "VALID"
