import json
from pathlib import Path


def select_action(delivered_state):
    if delivered_state in {"A", "B", "UNSAFE"}:
        return delivered_state
    return "ABSTAIN"


def run(visible):
    rows = []
    for case in visible["cases"]:
        for tick in case["ticks"]:
            observation_tick = tick["observation_tick"]
            comparable = tick["clock_comparable"] is True
            age = None
            if comparable and isinstance(observation_tick, int) and not isinstance(observation_tick, bool):
                age = tick["tick"] - observation_tick
                if age < 0:
                    age = None
            rows.append({
                "case_id": case["case_id"],
                "tick": tick["tick"],
                "opportunity_open": tick["opportunity_open"],
                "delivered_state": tick["delivered_state"],
                "observation_tick": observation_tick,
                "clock_comparable": comparable,
                "evidence_age": age,
                "admissible_actions": list(tick["admissible_actions"]),
                "selected_action": select_action(tick["delivered_state"]),
                "causal_use_identifiable": tick["causal_use_identifiable"],
                "delivered_observation_ids": list(tick.get("delivered_observation_ids", [])),
            })
    return {"schema": "decision-regret-8528-raw-v1", "rows": rows}


def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", default=".")
    args = parser.parse_args()
    root = Path(args.dir)
    visible = json.loads((root / "visible.json").read_text(encoding="utf-8"))
    raw = run(visible)
    (root / "candidate.json").write_text(json.dumps(raw, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"CANDIDATE_COMPLETE rows={len(raw['rows'])} cases={len(visible['cases'])}")


if __name__ == "__main__":
    main()
