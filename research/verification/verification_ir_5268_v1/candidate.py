"""Minimal authority-neutral Verification IR v0.1 candidate for Issue #5268."""

import json


TOP_FIELDS = {"schema", "unknown_check_required", "checks"}
CHECK_FIELDS = {
    "check_id", "primitive", "subject_ref", "criticality",
    "required_evidence_role", "verifier_class", "dependencies", "deadline",
    "budget_class", "fallback",
}
PRIMITIVES = {
    "TARGET.IDENTITY_CURRENT", "TARGET.TARGET_MATCH", "TARGET.AMBIGUITY",
    "SEMANTIC.INTENT_MATCH", "SEMANTIC.SCOPE_MATCH",
    "AUTHORITY.PERMISSION_CURRENT", "AUTHORITY.DECISION_DEADLINE",
    "EFFECT.REVERSIBILITY", "EFFECT.POSTCONDITION", "META.UNKNOWN_REQUIRED",
    "META.COVERAGE",
}
ROLES = {
    "CURRENT_OBSERVATION", "CURRENT_INTENT", "CURRENT_PERMISSION",
    "CURRENT_CLOCK", "CURRENT_ACTION_CONTRACT", "VERIFIED_EFFECT",
    "UNKNOWN_REQUIREMENT", "COVERAGE_REPORT",
}
CRITICALITIES = {"MANDATORY", "CONDITIONAL_MANDATORY", "OPTIONAL"}
ACTION_FIELDS = {
    "action_id", "target_ref", "expected_target_ref", "intent_ref",
    "target_ambiguous", "scope_changed", "deadline_expired",
    "permission_current", "external_side_effect", "effect_already_satisfied",
    "evidence_unknown", "diagnostic_requested",
}


def _check(check_id, primitive, subject_ref, role, verifier, dependencies=(),
           criticality="MANDATORY"):
    return {
        "check_id": check_id,
        "primitive": primitive,
        "subject_ref": subject_ref,
        "criticality": criticality,
        "required_evidence_role": role,
        "verifier_class": verifier,
        "dependencies": list(dependencies),
        "deadline": None,
        "budget_class": "bounded",
        "fallback": "YIELD_NO_INPUT",
    }


def lower_action(action):
    if set(action) != ACTION_FIELDS:
        raise ValueError("action fields must match the frozen v0.1 fixture schema")
    for name in ACTION_FIELDS - {"action_id", "target_ref", "expected_target_ref", "intent_ref"}:
        if type(action[name]) is not bool:
            raise ValueError(f"{name} must be Boolean")
    for name in ("action_id", "target_ref", "expected_target_ref", "intent_ref"):
        if not isinstance(action[name], str) or not action[name]:
            raise ValueError(f"{name} must be a nonempty string")

    checks = [
        _check("target.current", "TARGET.IDENTITY_CURRENT", action["target_ref"],
               "CURRENT_OBSERVATION", "fresh_target_observer"),
        _check("intent.match", "SEMANTIC.INTENT_MATCH", action["intent_ref"],
               "CURRENT_INTENT", "intent_contract", ("target.current",)),
    ]
    if action["target_ambiguous"]:
        checks.append(_check("target.ambiguity", "TARGET.AMBIGUITY", action["target_ref"],
                             "CURRENT_OBSERVATION", "ambiguity_detector", ("target.current",)))
    if action["target_ref"] != action["expected_target_ref"]:
        checks.append(_check("target.match", "TARGET.TARGET_MATCH", action["expected_target_ref"],
                             "CURRENT_OBSERVATION", "target_correspondence", ("target.current",)))
    if action["scope_changed"]:
        checks.append(_check("intent.scope", "SEMANTIC.SCOPE_MATCH", action["intent_ref"],
                             "CURRENT_INTENT", "scope_contract", ("intent.match",)))
    if action["deadline_expired"]:
        checks.append(_check("authority.deadline", "AUTHORITY.DECISION_DEADLINE", action["action_id"],
                             "CURRENT_CLOCK", "monotonic_deadline"))
    if not action["permission_current"]:
        checks.append(_check("authority.permission", "AUTHORITY.PERMISSION_CURRENT", action["target_ref"],
                             "CURRENT_PERMISSION", "permission_contract", ("target.current",)))
    if action["external_side_effect"]:
        checks.append(_check("effect.reversibility", "EFFECT.REVERSIBILITY", action["action_id"],
                             "CURRENT_ACTION_CONTRACT", "effect_policy"))
        checks.append(_check("effect.postcondition", "EFFECT.POSTCONDITION", action["target_ref"],
                             "VERIFIED_EFFECT", "independent_effect", ("target.current",)))
    elif action["effect_already_satisfied"]:
        checks.append(_check("effect.postcondition", "EFFECT.POSTCONDITION", action["target_ref"],
                             "VERIFIED_EFFECT", "independent_effect", ("target.current",),
                             "CONDITIONAL_MANDATORY"))
    if action["evidence_unknown"]:
        checks.append(_check("meta.unknown", "META.UNKNOWN_REQUIRED", action["action_id"],
                             "UNKNOWN_REQUIREMENT", "ontology_gap"))
    if action["diagnostic_requested"]:
        checks.append(_check("meta.coverage", "META.COVERAGE", action["action_id"],
                             "COVERAGE_REPORT", "coverage_report", (), "OPTIONAL"))

    result = {
        "schema": "verification_ir.v0.1",
        "unknown_check_required": action["evidence_unknown"],
        "checks": checks,
    }
    return validate_ir(json.loads(json.dumps(result, sort_keys=True)))


def validate_ir(ir):
    if not isinstance(ir, dict) or set(ir) != TOP_FIELDS:
        raise ValueError("IR fields do not match the authority-neutral v0.1 schema")
    if ir["schema"] != "verification_ir.v0.1" or type(ir["unknown_check_required"]) is not bool:
        raise ValueError("unsupported schema or malformed unknown-check marker")
    if not isinstance(ir["checks"], list):
        raise ValueError("checks must be a list")
    ids = set()
    for check in ir["checks"]:
        if not isinstance(check, dict) or set(check) != CHECK_FIELDS:
            raise ValueError("check fields do not match the v0.1 schema")
        if not isinstance(check["primitive"], str) or check["primitive"] not in PRIMITIVES:
            raise ValueError("unknown primitive")
        if not isinstance(check["required_evidence_role"], str) or check["required_evidence_role"] not in ROLES:
            raise ValueError("unknown evidence role")
        if not isinstance(check["criticality"], str) or check["criticality"] not in CRITICALITIES:
            raise ValueError("unknown criticality")
        if not all(isinstance(check[key], str) and check[key]
                   for key in ("check_id", "subject_ref", "verifier_class", "budget_class", "fallback")):
            raise ValueError("check identifiers and contract strings must be nonempty")
        if not isinstance(check["dependencies"], list) or not all(isinstance(x, str) for x in check["dependencies"]):
            raise ValueError("dependencies must be string identifiers")
        if check["deadline"] is not None and (type(check["deadline"]) is not int or check["deadline"] < 0):
            raise ValueError("deadline must be a nonnegative integer or null")
        if check["check_id"] in ids:
            raise ValueError("duplicate check identity")
        ids.add(check["check_id"])
    for check in ir["checks"]:
        if check["check_id"] in check["dependencies"] or not set(check["dependencies"]).issubset(ids):
            raise ValueError("self or unresolved dependency")
    has_unknown = any(c["primitive"] == "META.UNKNOWN_REQUIRED" for c in ir["checks"])
    if has_unknown != ir["unknown_check_required"]:
        raise ValueError("unsupported requirement marker cannot be hidden")
    return ir
