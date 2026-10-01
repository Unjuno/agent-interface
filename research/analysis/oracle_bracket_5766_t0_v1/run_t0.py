"""Finite synthetic check-standard experiment; no application or model calls."""
import json
from scorer_v1 import score


def run(spec):
    out = {"schema": "oracle-bracket-5766-raw-v1",
           "reference_timestamp": spec["reference_timestamp"], "scenarios": {}}
    deck = spec["check_deck"]
    for name, scenario in spec["scenarios"].items():
        pre = [score(item["record"]) for item in deck]
        post = list(pre)
        if scenario["drift_case"]:
            index = next(i for i, item in enumerate(deck)
                         if item["id"] == scenario["drift_case"])
            # App emits a well-formed but semantically changed artifact; scorer bytes stay fixed.
            post[index] = score(scenario["post_record"])
        candidate = [{"id": row["id"], "scored": score(row["record"]),
                      "reference": scenario.get("candidate_truth_overrides", {}).get(row["id"], row["reference"])}
                     for row in spec["candidate_rows"]]
        out["scenarios"][name] = {
            "scorer_sha256": spec["scorer_sha256"],
            "scorer_version": scenario["scorer_version"],
            "precheck": pre, "postcheck": post,
            "candidate_rows": candidate,
            "outside_deck": scenario["outside_deck"],
            "promotion": "UNKNOWN_COVERAGE" if scenario["outside_deck"] else
                        "HOLD_ORACLE_DRIFT" if post != pre else "PASS"
        }
    return out


if __name__ == "__main__":
    with open("spec.json", encoding="utf-8") as f:
        data = json.load(f)
    with open("raw.json", "w", encoding="utf-8", newline="\n") as f:
        json.dump(run(data), f, sort_keys=True, indent=2)
        f.write("\n")
