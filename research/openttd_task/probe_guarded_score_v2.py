"""Regression and malformed-input controls for geometry-derived guarded scoring."""
import copy
import json
from pathlib import Path

from guarded_score_v2 import score

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent / "live_control/results/timing-envelope-openttd-matched-04/fixed-astra/runtime"


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def rejected(baseline, observation):
    try:
        score(observation, baseline)
    except ValueError:
        return True
    return False


def main():
    evaluation = read(ROOT / "evaluation.json")
    baseline = evaluation["baseline"]
    complete = evaluation["observation"]
    initial = read(ROOT / "initial-evaluation.json")["observation"]
    positive = score(complete, baseline)
    negative = score(initial, baseline)
    assert positive["success"] is True
    assert negative["success"] is False
    assert positive["contract"]["target"] == [678, 679, 680]
    assert positive["contract"]["forbidden"] == [742, 743, 744]

    controls = {}
    case = copy.deepcopy(complete)
    case["x"] += 1
    controls["changed_x_rejected"] = rejected(baseline, case)
    case = copy.deepcopy(complete)
    case["width"] += 1
    controls["changed_width_rejected"] = rejected(baseline, case)
    case = copy.deepcopy(complete)
    case["guard"].pop()
    controls["missing_guard_rejected"] = rejected(baseline, case)
    case = copy.deepcopy(complete)
    case["guard"][0]["id"] = 999999
    controls["unexpected_guard_id_rejected"] = rejected(baseline, case)
    case = copy.deepcopy(complete)
    target = case["tiles"][0]["id"]
    next(tile for tile in case["guard"] if tile["id"] == target)["owner"] = -1
    controls["contradictory_overlap_rejected"] = rejected(baseline, case)
    case = copy.deepcopy(complete)
    surrounding = next(
        tile
        for tile in case["guard"]
        if tile["id"] not in positive["contract"]["target"]
        and tile["id"] not in positive["contract"]["forbidden"]
    )
    surrounding["owner"] = 7
    changed = score(case, baseline)
    controls["surrounding_change_fails"] = (
        changed["success"] is False
        and changed["changed_surrounding_tiles"] == [surrounding["id"]]
    )
    assert all(controls.values())
    result = {
        "probe_passed": True,
        "archived_positive_preserved": True,
        "archived_negative_preserved": True,
        "derived_contract": positive["contract"],
        "controls": controls,
    }
    path = HERE / "results/guarded-score-v2-probe.json"
    path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
