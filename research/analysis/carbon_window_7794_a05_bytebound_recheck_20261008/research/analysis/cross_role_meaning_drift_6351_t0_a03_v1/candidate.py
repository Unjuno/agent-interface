import json
import sys


def verdict(h):
    if h["source_epoch"] != h["verify_epoch"] or h["receipt_conflict"]:
        return "CONFLICT_NOT_PASS"
    if h["verification"] == "VERIFIED" and h["children"]:
        return "VERIFIED_WITH_CHILD_OBLIGATION"
    return h["verification"] if h["verification"] != "NOT_RUN" else "NOT_VERIFIED"


def run(path):
    histories = json.load(open(path, encoding="utf-8"))["histories"]
    rows = []
    for h in histories:
        v = verdict(h)
        role_projection = {
            "planner": "DISPATCH_UNKNOWN" if h["dispatch"] == "UNKNOWN" else "DISPATCH_ACCEPTED",
            "verifier": v,
            "effect_owner": {"release": h["release"], "effect": h["effect"], "children": h["children"], "epoch_conflict": h["source_epoch"] != h["verify_epoch"] or h["receipt_conflict"]},
        }
        # Negative control collapses any VERIFIED bit to whole-task completion.
        rows.append({"id": h["id"], "flattened": "COMPLETED" if h["verification"] == "VERIFIED" else v,
                     "typed": v, "projection": role_projection})
    return rows


if __name__ == "__main__":
    print(json.dumps(run(sys.argv[1]), sort_keys=True, separators=(",", ":")))
