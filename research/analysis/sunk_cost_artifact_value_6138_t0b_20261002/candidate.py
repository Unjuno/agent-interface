import json
import sys
from fractions import Fraction

FORWARD_FIELDS = ("present_state", "surviving_artifacts", "artifact_applicability",
                  "future_success_evidence", "remaining_deadline", "remaining_budget",
                  "safe_actions", "options")


def decide(card):
    values = {}
    for action in card["safe_actions"]:
        option = card["options"].get(action)
        if not option or any(option.get(k) is None for k in ("success_probability", "reward", "future_cost")):
            return {"choice": "UNKNOWN", "values": {}}
        probability = Fraction(option["success_probability"])
        if probability < 0 or probability > 1:
            return {"choice": "UNKNOWN", "values": {}}
        values[action] = probability * option["reward"] - option["future_cost"]
    if not values:
        return {"choice": "UNKNOWN", "values": {}}
    best = max(values.values())
    winners = [action for action, value in values.items() if value == best]
    return {"choice": winners[0] if len(winners) == 1 else "NO_PREFERENCE",
            "values": {action: str(value) for action, value in values.items()}}


def equivalent(left, right):
    return all(left.get(field) == right.get(field) for field in FORWARD_FIELDS)


def run(data):
    cards = {card["id"]: card for card in data["cards"]}
    results = {key: decide(card) for key, card in cards.items()}
    pairs = {}
    for pair in data["pairs"]:
        left, right = cards[pair["left"]], cards[pair["right"]]
        matches = equivalent(left, right)
        pairs[pair["id"]] = {
            "forward_equivalent": matches,
            "decision_invariant": (results[left["id"]]["choice"] == results[right["id"]]["choice"]) if matches else None,
            "accepted_as_matched": matches == pair["expect_forward_equivalent"],
        }
    return {"schema": "sunk-cost-artifact-value-result-t0b-v1", "cards": results, "pairs": pairs}


if __name__ == "__main__":
    source, destination = sys.argv[1:3]
    with open(source, encoding="utf-8") as stream:
        result = run(json.load(stream))
    with open(destination, "w", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2, sort_keys=True)
        stream.write("\n")
