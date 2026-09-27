"""Small deterministic SkillPackage validator and bounded proposal executor."""
from __future__ import annotations

import hashlib
import json
from typing import Any

REQUIRED = {
    "schema", "skill_id", "intent_version", "state_schema", "allowed_actions",
    "forbidden_effects", "predicates", "decision_choices", "macro_bindings",
    "yield_conditions", "progress_contract", "source_adapter_version", "validation_scope",
}
ACTION_VOCAB = {"SET_FIELD", "CLICK", "WAIT", "YIELD", "NO_ACTION"}
RULE_KEYS = {"kind", "field", "target", "effect", "forbidden"}


def canonical_bytes(value: dict[str, Any]) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode()


def validate_package(value: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(value, dict) or set(value) != REQUIRED:
        return ["PACKAGE_SHAPE"]
    if value["schema"] != "agent-interface-skill-package-v1":
        errors.append("PACKAGE_SCHEMA")
    for key in ("skill_id", "intent_version", "source_adapter_version"):
        if not isinstance(value[key], str) or not value[key]:
            errors.append("PACKAGE_" + key.upper())
    for key in ("state_schema", "allowed_actions", "forbidden_effects", "predicates", "decision_choices", "yield_conditions", "validation_scope"):
        if not isinstance(value[key], list) or any(not isinstance(v, str) or not v for v in value[key]) or len(set(value[key])) != len(value[key]):
            errors.append("PACKAGE_" + key.upper())
    if not set(value.get("allowed_actions", [])) <= ACTION_VOCAB:
        errors.append("PACKAGE_UNKNOWN_ACTION")
    if not set(value.get("decision_choices", [])) <= set(value.get("allowed_actions", [])):
        errors.append("CHOICE_OUTSIDE_PACKAGE_ACTIONS")
    if not isinstance(value.get("progress_contract"), dict) or set(value["progress_contract"]) != {"max_steps", "completion_effects"}:
        errors.append("PROGRESS_CONTRACT_SHAPE")
    else:
        steps = value["progress_contract"]["max_steps"]
        if not isinstance(steps, int) or isinstance(steps, bool) or not 1 <= steps <= 4:
            errors.append("PROGRESS_CONTRACT_STEP_BOUND")
        if not isinstance(value["progress_contract"]["completion_effects"], list):
            errors.append("PROGRESS_CONTRACT_EFFECTS")
    bindings = value.get("macro_bindings")
    if not isinstance(bindings, dict) or not bindings:
        errors.append("MACRO_BINDINGS")
    else:
        for name, rule in bindings.items():
            if not isinstance(name, str) or not isinstance(rule, dict) or set(rule) != RULE_KEYS:
                errors.append("MACRO_RULE_SHAPE:" + str(name))
                continue
            if rule["kind"] not in {"toggle", "field", "forbidden", "ambiguous"}:
                errors.append("MACRO_RULE_KIND:" + name)
            if rule["kind"] in {"toggle", "field"} and (not isinstance(rule["field"], str) or not isinstance(rule["target"], str) or not isinstance(rule["effect"], str)):
                errors.append("MACRO_RULE_FIELDS:" + name)
            if not isinstance(rule["forbidden"], bool):
                errors.append("MACRO_RULE_FORBIDDEN:" + name)
    return errors


def _emit(name: str, **arguments: Any) -> dict[str, Any]:
    return {"name": name, "arguments": arguments}


def propose(package: dict[str, Any], request: dict[str, Any], state: dict[str, Any], authority: dict[str, Any]) -> dict[str, Any]:
    """Return one shadow proposal. This function never mutates state or grants authority."""
    def yield_(reason: str) -> dict[str, Any]:
        return _emit("YIELD", reason=reason)

    if request.get("intent_version") != package.get("intent_version"):
        return yield_("stale_scope")
    if request.get("scope_id") != state.get("scope_id") or request.get("scope_id") != authority.get("scope_id"):
        return yield_("stale_scope")
    if request.get("generation") != state.get("generation") or request.get("generation") != authority.get("generation"):
        return yield_("stale_scope")
    if state.get("freshness") != "fresh":
        return yield_("missing_evidence")
    if state.get("ambiguous"):
        return yield_("ambiguous")
    rule = package.get("macro_bindings", {}).get(request.get("intent"))
    if rule is None:
        return yield_("unsupported")
    if rule["kind"] == "forbidden" or rule["forbidden"]:
        return yield_("forbidden")
    if rule["kind"] == "ambiguous":
        return yield_("ambiguous")

    actions = set(package.get("allowed_actions", ())) & set(authority.get("allowed_actions", ()))
    effects = set(authority.get("allowed_effects", ())) - set(package.get("forbidden_effects", ()))
    if rule["effect"] not in effects:
        return yield_("forbidden")
    if rule["kind"] == "toggle":
        field, desired = rule["field"], request.get("value")
        if not isinstance(desired, bool):
            return yield_("ambiguous")
        if state.get("values", {}).get(field) is desired:
            return _emit("NO_ACTION", reason="already_satisfied")
        if "CLICK" not in actions:
            return yield_("unsupported")
        if rule["target"] not in state.get("visible_targets", ()):
            return yield_("missing_evidence")
        return _emit("CLICK", scope_id=request["scope_id"], generation=request["generation"], target=rule["target"])

    if rule["kind"] == "field":
        desired = request.get("value")
        field = rule["field"]
        if not isinstance(desired, str) or desired not in state.get("allowed_values", {}).get(field, ()):
            return yield_("ambiguous")
        if state.get("values", {}).get(field) == desired and state.get("staged", {}).get(field) != desired:
            return _emit("NO_ACTION", reason="already_satisfied")
        if state.get("staged", {}).get(field) == desired:
            if "CLICK" not in actions or "save_settings" not in effects:
                return yield_("unsupported")
            if rule["target"] not in state.get("visible_targets", ()):
                return yield_("missing_evidence")
            return _emit("CLICK", scope_id=request["scope_id"], generation=request["generation"], target=rule["target"])
        if "SET_FIELD" not in actions:
            return yield_("unsupported")
        return _emit("SET_FIELD", scope_id=request["scope_id"], generation=request["generation"], field=field, value=desired)
    return yield_("unsupported")


class ActiveSkill:
    """Byte-backed snapshots make failed validation and rollback observable."""
    def __init__(self, active: dict[str, Any]):
        errors = validate_package(active)
        if errors:
            raise ValueError(errors)
        self._active = canonical_bytes(active)
        self._previous: bytes | None = None

    @property
    def active_bytes(self) -> bytes:
        return self._active

    @property
    def active_sha256(self) -> str:
        return hashlib.sha256(self._active).hexdigest()

    def package(self) -> dict[str, Any]:
        return json.loads(self._active)

    def install(self, candidate: Any) -> bool:
        if validate_package(candidate):
            return False
        self._previous = self._active
        self._active = canonical_bytes(candidate)
        return True

    def rollback(self) -> bool:
        if self._previous is None:
            return False
        self._active, self._previous = self._previous, None
        return True

