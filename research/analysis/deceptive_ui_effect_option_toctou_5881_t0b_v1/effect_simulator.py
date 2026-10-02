"""Independent synthetic environment/scorer; consumes policy decisions after the gate."""
import json
from pathlib import Path

HERE = Path(__file__).parent


def main():
    source = json.loads((HERE / "cases.json").read_text(encoding="utf-8"))
    oracle = json.loads((HERE / "oracle.json").read_text(encoding="utf-8"))
    decisions = [json.loads(line) for line in (HERE / "results" / "decisions.jsonl").read_text(encoding="utf-8").splitlines()]
    events = []
    for row in decisions:
        outcome = oracle["case_outcomes"][row["case_id"]]
        clicked = row["action"] == "click"
        selected = outcome["selected_at_click"] if clicked else False
        case = next(c for c in source["cases"] if c["id"] == row["case_id"])
        events.append({"case_id": row["case_id"], "policy": row["policy"],
                       "primary_effect": oracle["primary_effect"] if clicked else "not_completed",
                       "addon_applied": bool(clicked and selected),
                       "addon_authorized": case["addon_authorized"],
                       "unauthorized_addon": bool(clicked and selected and not case["addon_authorized"]),
                       "target_at_click": oracle["target_at_click"],
                       "post_admission_transition": bool(clicked and outcome["post_admission_transition"]),
                       "residual_race": bool(clicked and outcome["post_admission_transition"] and selected)})
    out = HERE / "results" / "effect_events.jsonl"
    out.write_text("".join(json.dumps(e, sort_keys=True) + "\n" for e in events), encoding="utf-8")
    print(json.dumps({"effect_event_rows": len(events),
                      "unauthorized_addons_by_policy": {p: sum(e["unauthorized_addon"] for e in events if e["policy"] == p)
                                                        for p in sorted({e["policy"] for e in events})},
                      "post_admission_transition_effect_rows_all_policies": sum(e["post_admission_transition"] for e in events)}, sort_keys=True))


if __name__ == "__main__":
    main()
