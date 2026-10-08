"""Candidate computation for Issue #8057 finite method fixture."""
import json
from pathlib import Path

ARMS = ("NEITHER", "PRIVATE_NOTE", "ENVIRONMENT_CUE", "BOTH")


def run(fixture):
    result = []
    for case in fixture["scenarios"]:
        for arm in fixture["arms"]:
            note_arm = arm in ("PRIVATE_NOTE", "BOTH")
            cue_arm = arm in ("ENVIRONMENT_CUE", "BOTH")
            note_write = 2 if note_arm and any(not s["note"]["omitted"] for s in case["steps"]) else 0
            steps = []
            for index, step in enumerate(case["steps"]):
                cost = {k: 0 for k in ("note_write", "note_read", "context_units", "ui_setup", "ui_observation", "cleanup", "recovery", "rediscovery")}
                if index == 0:
                    cost["note_write"] = note_write
                if cue_arm:
                    cost["ui_setup"] = case["ui_setup"] if index == 0 else 0
                    cost["ui_observation"] = case["ui_observation"]
                    if index == len(case["steps"]) - 1:
                        cost["cleanup"] = case["ui_cleanup"] if case.get("restore_succeeds", True) else 0
                        cost["recovery"] = 0 if case.get("restore_succeeds", True) else case["ui_recovery"]
                common = step["common_fact"] == step["fact"]
                note = step["note"]
                note_present = note_arm and not note["omitted"]
                note_fresh = note_present and note["task"] == step["task"] and note["fact"] == step["fact"] and note["source_version"] == step["fact_version"]
                if note_present and not common:
                    cost["note_read"] = 1
                    cost["context_units"] = 2
                cue = step["cue"]
                cue_present = cue_arm and cue["visible"]
                cue_fresh = cue_present and cue["task"] == step["task"] and cue["fact"] == step["fact"] and cue["generation"] == step["app_generation"] and cue["adds_info"]
                if common:
                    source = "COMMON_OBSERVATION"
                elif note_fresh:
                    source = "PRIVATE_NOTE"
                elif cue_fresh:
                    source = "ENVIRONMENT_CUE"
                elif case["rediscovery_succeeds"]:
                    source = "SAFE_REDISCOVERY"
                    cost["rediscovery"] = case["rediscovery_cost"]
                else:
                    source = "UNRESOLVED"
                    cost["rediscovery"] = case["rediscovery_cost"]
                warning_visible = not (cue_present and cue["obscures_warning"])
                restoration_ok = not cue_arm or case.get("restore_succeeds", True)
                steps.append({"case_id": case["id"], "arm": arm, "step_id": step["id"],
                              "source": source, "task_correct": source != "UNRESOLVED",
                              "warning_visible": warning_visible, "restoration_ok": restoration_ok,
                              "safety_pass": warning_visible and restoration_ok, "cost": cost,
                              "total_cost": sum(cost.values())})
            result.extend(steps)
    return result


if __name__ == "__main__":
    fixture = json.loads(Path("fixture.json").read_text(encoding="utf-8"))
    print(json.dumps(run(fixture), sort_keys=True, separators=(",", ":")))
