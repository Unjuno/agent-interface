import json
import sys
from fractions import Fraction

FIELDS = ("present_state", "surviving_artifacts", "artifact_applicability",
          "future_success_evidence", "remaining_deadline", "remaining_budget",
          "safe_actions", "options")


def reconstruct(card):
    values = {}
    for action in card["safe_actions"]:
        option = card["options"].get(action)
        if not option or any(option.get(k) is None for k in ("success_probability", "reward", "future_cost")):
            return "UNKNOWN", {}
        probability = Fraction(option["success_probability"])
        if probability < 0 or probability > 1:
            return "UNKNOWN", {}
        values[action] = probability * option["reward"] - option["future_cost"]
    if not values:
        return "UNKNOWN", {}
    best = max(values.values())
    winners = [action for action, value in values.items() if value == best]
    return (winners[0] if len(winners) == 1 else "NO_PREFERENCE"), {k: str(v) for k, v in values.items()}


def audit(data, output):
    errors = []
    cards = {card["id"]: card for card in data["cards"]}
    actual_cards = output.get("cards", {})
    if set(cards) != set(actual_cards):
        errors.append("card_set")
    for key, card in cards.items():
        expected_choice, expected_values = reconstruct(card)
        actual = actual_cards.get(key, {})
        if actual.get("choice") != expected_choice or actual.get("values") != expected_values:
            errors.append("oracle:" + key)
    pairs = output.get("pairs", {})
    if set(pairs) != {pair["id"] for pair in data["pairs"]}:
        errors.append("pair_set")
    for pair in data["pairs"]:
        left, right = cards[pair["left"]], cards[pair["right"]]
        equal = all(left.get(field) == right.get(field) for field in FIELDS)
        actual = pairs.get(pair["id"], {})
        if equal != pair["expect_forward_equivalent"] or actual.get("forward_equivalent") != equal:
            errors.append("equivalence:" + pair["id"])
        if actual.get("accepted_as_matched") is not (equal == pair["expect_forward_equivalent"]):
            errors.append("pair_acceptance:" + pair["id"])
        if equal and actual.get("decision_invariant") is not True:
            errors.append("invariance:" + pair["id"])
        if not equal and actual.get("decision_invariant") is not None:
            errors.append("invalid_invariance:" + pair["id"])
    return {"status": "PASS_METHOD_SCOPED" if not errors else "FAIL",
            "cards_reconstructed": len(cards), "pairs_reconstructed": len(data["pairs"]), "errors": errors}


if __name__ == "__main__":
    source, output_path, destination = sys.argv[1:4]
    data = json.load(open(source, encoding="utf-8"))
    result = audit(data, json.load(open(output_path, encoding="utf-8")))
    json.dump(result, open(destination, "w", encoding="utf-8"), indent=2, sort_keys=True)
    open(destination, "a", encoding="utf-8").write("\n")
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if not result["errors"] else 1)
