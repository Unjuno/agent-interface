import json
import sys


def classify(row):
    covered = (
        set(row["required_writers"]) == set(row["enrolled_writers"])
        and row["epoch_ok"]
        and row["sequence_complete"]
    )
    if not covered:
        frontier = "UNKNOWN"
    elif row["predicate_change_before_F"] or row["value_A"] != row["value_F"]:
        frontier = "CHANGE_OBSERVED"
    else:
        frontier = "QUIET_AS_OF_FRONTIER"
    actuation = "ADMIT" if frontier == "QUIET_AS_OF_FRONTIER" and row["atomic_compare_at_B"] and row["version_F"] == row["version_B"] else "BLOCK"
    return {"case_id": row["id"], "frontier": frontier, "actuation": actuation}


def main():
    fixture = json.load(open(sys.argv[1], encoding="utf-8"))
    result = {row["id"]: classify(row) for row in fixture["cases"]}
    print(json.dumps({"schema": "6310-candidate-v1", "results": result}, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
