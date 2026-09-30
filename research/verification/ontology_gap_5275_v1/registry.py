"""Conservative deterministic ontology-gap detector for frozen Agent Action plans."""
KNOWN_PRIMITIVES = frozenset({
    "AUTHORITY.SCOPE_CURRENT",
    "TARGET.IDENTITY_CURRENT",
    "EFFECT.POSTCONDITION",
    "EFFECT.REVERSIBILITY",
    "SECURITY.PERMISSION_CURRENT",
    "SEMANTIC.INTENT_MATCH",
    "FACT.SOURCE_SUPPORT",
})
KNOWN_EVIDENCE_ROLES = frozenset({
    "OBSERVATION_CURRENT",
    "INDEPENDENT_EFFECT",
    "POLICY_RECORD",
})
KNOWN_VERIFIERS = frozenset({
    "deterministic_rule",
    "local_cpu",
    "local_multimodal_placeholder",
    "rich_model",
    "external_tool",
})

def classify(plan):
    """Return UNKNOWN_CHECK_REQUIRED or PLAN_COVERED; never an action verdict."""
    if not isinstance(plan, dict) or plan.get("plan_version") != "v0.1":
        return "UNKNOWN_CHECK_REQUIRED"
    checks = plan.get("checks")
    if not isinstance(checks, list) or not checks:
        return "UNKNOWN_CHECK_REQUIRED"
    for check in checks:
        if not isinstance(check, dict):
            return "UNKNOWN_CHECK_REQUIRED"
        if check.get("primitive") not in KNOWN_PRIMITIVES:
            return "UNKNOWN_CHECK_REQUIRED"
        if check.get("evidence_role") not in KNOWN_EVIDENCE_ROLES:
            return "UNKNOWN_CHECK_REQUIRED"
        if check.get("verifier_class") not in KNOWN_VERIFIERS:
            return "UNKNOWN_CHECK_REQUIRED"
        if not isinstance(check.get("subject_ref"), str) or not check["subject_ref"]:
            return "UNKNOWN_CHECK_REQUIRED"
        if not isinstance(check.get("version"), str) or not check["version"]:
            return "UNKNOWN_CHECK_REQUIRED"
    return "PLAN_COVERED"
