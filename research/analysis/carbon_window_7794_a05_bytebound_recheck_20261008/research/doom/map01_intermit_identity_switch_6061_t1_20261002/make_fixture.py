"""Deterministically construct planner-visible and auditor-only identity-switch traces."""
import json
from pathlib import Path


OUT = Path(__file__).parent
N = 12
SWITCH = 5
CASES = ("same_identity_control", "visible_identity_switch",
         "epoch_only_switch", "unknown_epoch_switch", "silent_identity_switch")


def build():
    visible, truth = [], []
    for case_id in CASES:
        rows, truth_rows = [], []
        for tick in range(N):
            changed = case_id != "same_identity_control" and tick >= SWITCH
            obs_id = "target-B" if case_id == "visible_identity_switch" and changed else "target-A"
            epoch = 18 if case_id in ("visible_identity_switch", "epoch_only_switch") and changed else 17
            if case_id == "unknown_epoch_switch" and changed:
                epoch = None
            if case_id == "unknown_epoch_switch" and changed:
                obs_id = None
            rows.append({
                "tick": tick,
                "observed_identity": obs_id,
                "observed_epoch": epoch,
                "focus_valid": True,
                "lease_valid": True,
                "prediction_error": 0.0,
                "predicted_direction": 1,
            })
            truth_rows.append({
                "tick": tick,
                "target_identity": "target-B" if changed else "target-A",
                "target_epoch": 18 if changed else 17,
            })
        visible.append({
            "case_id": case_id,
            "intended_identity": "target-A",
            "intended_epoch": 17,
            "observations": rows,
        })
        truth.append({"case_id": case_id, "states": truth_rows,
                      "switch_tick": None if case_id == "same_identity_control" else SWITCH})
    return {"schema": "agent-interface.intermit6061.identity-switch.input.v1", "cases": visible}, {
        "schema": "agent-interface.intermit6061.identity-switch.truth.v1", "cases": truth}


def main():
    visible, truth = build()
    (OUT / "input.json").write_text(json.dumps(visible, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    (OUT / "truth.json").write_text(json.dumps(truth, sort_keys=True, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
