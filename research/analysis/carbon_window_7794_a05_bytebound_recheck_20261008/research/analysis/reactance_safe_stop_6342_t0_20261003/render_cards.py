#!/usr/bin/env python3
"""Render the frozen, synthetic #6342 T0 safe-stop cards."""

import argparse
import json
from pathlib import Path


def render(fixture: dict) -> dict:
    cards = []
    for case in fixture["cases"]:
        for arm, sentence in fixture["framing"].items():
            cards.append(
                {
                    "card_id": f"{case['case_id']}__{arm}",
                    "case_id": case["case_id"],
                    "arm": arm,
                    "title": case["title"],
                    "state": case["state"],
                    "evidence": case["evidence"],
                    "required_stop": case["required_stop"],
                    "allowed_actions": list(case["allowed_actions"]),
                    "receipt_ref": case["receipt_ref"],
                    "framing_line": sentence,
                    "accessibility": dict(fixture["accessibility_contract"]),
                }
            )

    controls = []
    for control in fixture["negative_controls"]:
        case = next(item for item in fixture["cases"] if item["case_id"] == control["case_id"])
        card = {
            "control_id": control["control_id"],
            "case_id": control["case_id"],
            "title": case["title"],
            "state": case["state"],
            "evidence": case["evidence"],
            "required_stop": case["required_stop"],
            "allowed_actions": list(case["allowed_actions"]),
            "receipt_ref": case["receipt_ref"],
            "framing_line": fixture["framing"]["directive"],
            "accessibility": dict(fixture["accessibility_contract"]),
        }
        if "mutated_allowed_action" in control:
            card["allowed_actions"].append(control["mutated_allowed_action"])
        if "mutated_status" in control:
            card["state"] = "claimed_success"
            card["status_message"] = control["mutated_status"]
        controls.append(card)
    return {"schema": "safe-stop-card-output-v1", "allocation_id": fixture["allocation_id"], "cards": cards, "negative_controls": controls}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", default="/input/cards.json")
    parser.add_argument("--output", default="/output/candidate.json")
    args = parser.parse_args()
    fixture = json.loads(Path(args.fixture).read_text(encoding="utf-8"))
    result = render(fixture)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"allocation_id": result["allocation_id"], "cards": len(result["cards"]), "negative_controls": len(result["negative_controls"]), "output": str(output)}, sort_keys=True))


if __name__ == "__main__":
    main()
