"""Regression probe for positive, bounded, and visual-false finish packaging."""
import json
from pathlib import Path

from openttd_finish_outcome_v1 import classify

HERE = Path(__file__).resolve().parent
BASE = HERE / "results/timing-envelope-openttd-matched-02"


def evaluation(arm):
    finish = json.loads((BASE / arm / "finish.json").read_text(encoding="utf-8"))
    return next(row for row in finish["reply"]["records"] if row["event"] == "independent_evaluation")


def main():
    positive_name, positive = classify(
        "proposal-7.json", evaluation("fixed-astra"), exit_code=0,
        proposals_executed=6, journal_calls=24, reason="verify", arm="fixed-astra"
    )
    assert positive_name == "result.json" and "evaluation" not in positive

    visual_name, visual = classify(
        "proposal-7.json", evaluation("adaptive"), exit_code=0,
        proposals_executed=6, journal_calls=24, reason="verify", arm="adaptive"
    )
    assert visual_name == "failure-evaluation.json"
    assert visual["failure_mode"] == "visual_verify_false_positive"
    assert visual["evaluation"]["success"] is False

    bounded_name, bounded = classify(
        "abort.json", evaluation("fixed-luna"), exit_code=0,
        proposals_executed=9, journal_calls=36, reason="bounded", arm="fixed-luna"
    )
    assert bounded_name == "failure-evaluation.json"
    assert bounded["failure_mode"] == "bounded_turn_limit"
    print("openttd_finish_outcome_probe_v1: PASS")


if __name__ == "__main__":
    main()
