"""Independent scorer/oracle audit. Does not import candidate policy code."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).parent
POLICIES = {"PLAIN", "TARGET_ONLY", "FRESH_EFFECT_BOUNDARY"}
PRE_GATE = {"pre_admission_flip", "effect_state_unavailable", "stale_effect_generation", "effect_read_integrity_mismatch"}
DECISION_FIELDS = {"case_id", "policy", "action", "admission", "reason"}


def expected_decision(policy, target, case):
    if policy == "PLAIN":
        return ("click", "ADMIT", "plain")
    if policy == "TARGET_ONLY":
        good = bool(target.get("id") and target.get("geometry"))
        return ("click", "ADMIT", "target_only") if good else ("yield", "YIELD_UNKNOWN", "target_unbound")
    if not case["current_readable"]:
        return ("yield", "YIELD_UNKNOWN", "effect_state_unavailable_or_unverified")
    if case["current_generation"] < case["descriptor_generation"]:
        return ("yield", "YIELD_UNKNOWN", "effect_state_older_than_descriptor")
    material = "target={}|effect={}|selected={}|generation={}".format(
        target["id"], case["effect_option_id"], str(case["current_selected"]).lower(), case["current_generation"])
    if case["read_digest"] != hashlib.sha256(material.encode("utf-8")).hexdigest():
        return ("yield", "YIELD_UNKNOWN", "effect_state_digest_mismatch")
    if case["current_selected"] and not case["addon_authorized"]:
        return ("yield", "BLOCK_UNAUTHORIZED_ADDON", "current_effect_exceeds_contract")
    return ("click", "ADMIT", "current_effect_within_contract")


def expected_event(decision, case, oracle):
    outcome = oracle["case_outcomes"][case["id"]]
    clicked = decision["action"] == "click"
    selected = bool(clicked and outcome["selected_at_click"])
    return {"case_id": case["id"], "policy": decision["policy"],
            "primary_effect": oracle["primary_effect"] if clicked else "not_completed",
            "addon_applied": selected, "addon_authorized": case["addon_authorized"],
            "unauthorized_addon": bool(selected and not case["addon_authorized"]),
            "target_at_click": oracle["target_at_click"],
            "post_admission_transition": bool(clicked and outcome["post_admission_transition"]),
            "residual_race": bool(clicked and outcome["post_admission_transition"] and selected)}


def verify(cases_doc, oracle, decisions, events):
    errors = []
    cases = cases_doc["cases"]
    case_map = {c["id"]: c for c in cases}
    if len(case_map) != 8 or set(case_map) != set(oracle["case_outcomes"]):
        errors.append("case/oracle inventory mismatch")
    target = cases_doc["target"]
    if oracle.get("target_at_click") != target:
        errors.append("target or geometry changed")
    keys = [(d.get("case_id"), d.get("policy")) for d in decisions]
    expected_keys = {(c["id"], p) for c in cases for p in POLICIES}
    if set(keys) != expected_keys or len(keys) != len(expected_keys):
        errors.append("missing or duplicate policy decision")
    dmap = {}
    for d in decisions:
        if set(d) != DECISION_FIELDS:
            errors.append(f"unexpected candidate-visible field(s): {d.get('case_id')}/{d.get('policy')}")
            continue
        if d.get("case_id") not in case_map or d.get("policy") not in POLICIES:
            errors.append("unknown case or policy")
            continue
        exp = expected_decision(d["policy"], target, case_map[d["case_id"]])
        got = (d.get("action"), d.get("admission"), d.get("reason"))
        if got != exp:
            errors.append(f"decision mismatch {d['case_id']}/{d['policy']}")
        dmap[(d["case_id"], d["policy"])] = d
    emap = {(e.get("case_id"), e.get("policy")): e for e in events}
    if len(emap) != len(events) or set(emap) != expected_keys:
        errors.append("effect event inventory mismatch")
    for key, decision in dmap.items():
        expected = expected_event(decision, case_map[key[0]], oracle)
        if emap.get(key) != expected:
            errors.append(f"scorer outcome mismatch {key[0]}/{key[1]}")

    fresh = [emap[(c["id"], "FRESH_EFFECT_BOUNDARY")] for c in cases if (c["id"], "FRESH_EFFECT_BOUNDARY") in emap]
    target_only = [emap[(c["id"], "TARGET_ONLY")] for c in cases if (c["id"], "TARGET_ONLY") in emap]
    plain = [emap[(c["id"], "PLAIN")] for c in cases if (c["id"], "PLAIN") in emap]
    pre_fresh = [e for e in fresh if e["case_id"] in PRE_GATE]
    pre_baseline = [e for e in target_only if e["case_id"] in PRE_GATE]
    if sum(e["unauthorized_addon"] for e in pre_fresh) != 0:
        errors.append("fresh effect gate allowed a pre-admission unauthorized add-on")
    if sum(e["unauthorized_addon"] for e in pre_baseline) != 4:
        errors.append("pre-admission target-only control not discriminating")
    authorized = emap.get(("authorized_deceptive_optin", "FRESH_EFFECT_BOUNDARY"), {})
    if authorized.get("primary_effect") != oracle["primary_effect"] or not authorized.get("addon_applied") or not authorized.get("addon_authorized"):
        errors.append("explicit authorized deceptive-looking option was suppressed")
    residual = [e for e in fresh if e["residual_race"]]
    if len(residual) != 1 or residual[0]["case_id"] != "post_admission_flip" or not residual[0]["unauthorized_addon"]:
        errors.append("non-atomic post-admission race was omitted or mislabeled")
    if sum(e["unauthorized_addon"] for e in fresh) != 1:
        errors.append("fresh gate's residual unauthorized effect count mismatch")
    if not all(c["id"] in case_map for c in cases):
        errors.append("case keys malformed")
    disposition = "METHOD_PASS_SCOPED_WITH_RESIDUAL_RACE" if not errors else "METHOD_FAIL"
    return {"disposition": disposition, "case_count": len(cases), "policy_decisions": len(decisions),
            "effect_events": len(events),
            "unauthorized_addons": {"PLAIN": sum(e["unauthorized_addon"] for e in plain),
                                    "TARGET_ONLY": sum(e["unauthorized_addon"] for e in target_only),
                                    "FRESH_EFFECT_BOUNDARY": sum(e["unauthorized_addon"] for e in fresh)},
            "pre_admission_unauthorized_addons": {"TARGET_ONLY": sum(e["unauthorized_addon"] for e in pre_baseline),
                                                  "FRESH_EFFECT_BOUNDARY": sum(e["unauthorized_addon"] for e in pre_fresh)},
            "authorized_optin_completed": bool(authorized.get("addon_applied") and authorized.get("addon_authorized")),
            "residual_post_admission_races": len(residual), "errors": errors,
            "scope": "deterministic synthetic effect-boundary method check only"}


def read_jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def main():
    results = HERE / "results"
    cases = json.loads((HERE / "cases.json").read_text(encoding="utf-8"))
    oracle = json.loads((HERE / "oracle.json").read_text(encoding="utf-8"))
    result = verify(cases, oracle, read_jsonl(results / "decisions.jsonl"), read_jsonl(results / "effect_events.jsonl"))
    (results / "audit.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    if result["errors"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
