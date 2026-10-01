import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).parent
OUT = Path("/out/formal01")


def minimax_regret(actions, rankings, profiles):
    if not rankings:
        return None, None
    regrets = {}
    for action in actions:
        regrets[action] = max(
            max(profiles[ranking][candidate] for candidate in actions)
            - profiles[ranking][action]
            for ranking in rankings
        )
    minimum = min(regrets.values())
    best = sorted(action for action, regret in regrets.items() if regret == minimum)
    return best[0], minimum


def decide(case, fixture):
    admissible = [a for a in case["admissible"] if a not in case["forbidden"]]
    if not admissible:
        return {"outcome": "YIELD", "action": None, "reason": "NO_ADMISSIBLE_ACTION", "minimax_regret": None}
    if case["state"] == "constructing":
        if not case["neutral_explanation"]:
            return {"outcome": "HOLD_PREF_NOT_FORMED", "action": None, "reason": "NO_NEUTRAL_EXPLANATION", "minimax_regret": None}
        if case["response"] is None:
            return {"outcome": "YIELD", "action": None, "reason": "NO_RESPONSE", "minimax_regret": None}
        if case["response_version"] != case["choice_version"]:
            return {"outcome": "YIELD", "action": None, "reason": "STALE_CHOICE_VERSION", "minimax_regret": None}
        if case["framing_answers"] and len(set(case["framing_answers"])) > 1:
            return {"outcome": "HOLD_FRAMING_SENSITIVE", "action": None, "reason": "FRAMING_DISAGREEMENT", "minimax_regret": None}
        preferred = max(admissible, key=lambda a: fixture["preference_profiles"][case["response"]][a])
        return {"outcome": "SCOPED_SELECTION", "action": preferred, "reason": "CHOICE_BOUND_ANSWER", "minimax_regret": None}
    if case["framing_answers"] and len(set(case["framing_answers"])) > 1:
        return {"outcome": "HOLD_FRAMING_SENSITIVE", "action": None, "reason": "FRAMING_DISAGREEMENT", "minimax_regret": None}
    robust, regret = minimax_regret(admissible, case["rankings"], fixture["preference_profiles"])
    if regret is not None and regret <= fixture["regret_threshold"]:
        return {"outcome": "ACT", "action": robust, "reason": "ROBUST_WITHIN_THRESHOLD", "minimax_regret": regret}
    if case["query_cost"] > min(case["deadline_budget"], fixture["deadline_budget"]):
        return {"outcome": "ACT", "action": case["authorized_default"], "reason": "EXPLICIT_AUTHORIZED_DEFAULT", "minimax_regret": regret} if case["authorized_default"] in admissible else {"outcome": "YIELD", "action": None, "reason": "NO_DEFAULT_BEFORE_DEADLINE", "minimax_regret": regret}
    if case["response"] is None:
        return {"outcome": "YIELD", "action": None, "reason": "NO_RESPONSE", "minimax_regret": regret}
    if case["response_version"] != case["choice_version"]:
        return {"outcome": "YIELD", "action": None, "reason": "STALE_CHOICE_VERSION", "minimax_regret": regret}
    if case["response"] not in fixture["preference_profiles"]:
        return {"outcome": "YIELD", "action": None, "reason": "UNSUPPORTED_RESPONSE", "minimax_regret": regret}
    action = max(admissible, key=lambda a: fixture["preference_profiles"][case["response"]][a])
    return {"outcome": "ASK_THEN_ACT", "action": action, "reason": "CHOICE_BOUND_ANSWER", "minimax_regret": regret}


def build_raw():
    fixture = json.loads((ROOT / "fixture.json").read_text(encoding="utf-8"))
    rows = []
    for case in fixture["cases"]:
        decision = decide(case, fixture)
        rows.append({"case_id": case["id"], **decision,
                     "expected": case["expected"], "expected_action": case["expected_action"],
                     "unsafe_or_forbidden": decision["action"] in case["forbidden"] if decision["action"] else False,
                     "counts_as_query": decision["outcome"] == "ASK_THEN_ACT"})
    return {"schema": "issue5749-preference-gate-raw-v1", "allocation": fixture["allocation"],
            "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "fixture_sha256": hashlib.sha256((ROOT / "fixture.json").read_bytes()).hexdigest(),
            "rows": rows}


def main():
    OUT.mkdir(parents=True, exist_ok=False)
    encoded = json.dumps(build_raw(), sort_keys=True, separators=(",", ":")) + "\n"
    (OUT / "raw.json").write_text(encoded, encoding="utf-8")
    print(json.dumps({"allocation": "5749-preference-gate-t0-20261001-01", "rows": len(json.loads(encoded)["rows"]),
                      "raw_sha256": hashlib.sha256(encoded.encode()).hexdigest()}, sort_keys=True))


if __name__ == "__main__":
    main()
