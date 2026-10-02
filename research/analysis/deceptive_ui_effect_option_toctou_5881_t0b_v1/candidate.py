"""Controller-visible policy simulation. Scorer-only oracle is not imported."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).parent
POLICIES = ("PLAIN", "TARGET_ONLY", "FRESH_EFFECT_BOUNDARY")


def decide(policy, target, case):
    if policy == "PLAIN":
        return {"action": "click", "admission": "ADMIT", "reason": "plain"}
    if policy == "TARGET_ONLY":
        return {"action": "click" if target.get("id") and target.get("geometry") else "yield",
                "admission": "ADMIT" if target.get("id") and target.get("geometry") else "YIELD_UNKNOWN",
                "reason": "target_only"}
    if policy != "FRESH_EFFECT_BOUNDARY":
        raise ValueError("unknown policy")
    if not case["current_readable"]:
        return {"action": "yield", "admission": "YIELD_UNKNOWN", "reason": "effect_state_unavailable_or_unverified"}
    if case["current_generation"] < case["descriptor_generation"]:
        return {"action": "yield", "admission": "YIELD_UNKNOWN", "reason": "effect_state_older_than_descriptor"}
    material = "target={}|effect={}|selected={}|generation={}".format(
        target["id"], case["effect_option_id"], str(case["current_selected"]).lower(), case["current_generation"])
    if case["read_digest"] != hashlib.sha256(material.encode("utf-8")).hexdigest():
        return {"action": "yield", "admission": "YIELD_UNKNOWN", "reason": "effect_state_digest_mismatch"}
    if case["current_selected"] and not case["addon_authorized"]:
        return {"action": "yield", "admission": "BLOCK_UNAUTHORIZED_ADDON", "reason": "current_effect_exceeds_contract"}
    return {"action": "click", "admission": "ADMIT", "reason": "current_effect_within_contract"}


def main():
    source = json.loads((HERE / "cases.json").read_text(encoding="utf-8"))
    path = HERE / "results" / "decisions.jsonl"
    path.parent.mkdir(exist_ok=True)
    rows = []
    for case in source["cases"]:
        for policy in POLICIES:
            rows.append({"case_id": case["id"], "policy": policy,
                         **decide(policy, source["target"], case)})
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")
    print(json.dumps({"decision_rows": len(rows), "case_count": len(source["cases"]),
                      "policy_count": len(POLICIES), "oracle_fields_read": 0}, sort_keys=True))


if __name__ == "__main__":
    main()
