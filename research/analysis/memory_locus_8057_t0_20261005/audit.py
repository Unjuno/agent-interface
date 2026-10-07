"""Independent finite-row enumerator; does not import candidate.py."""
import json
from pathlib import Path
import sys

ARMS = ("NEITHER", "PRIVATE_NOTE", "ENVIRONMENT_CUE", "BOTH")
COST_KEYS = ("note_write", "note_read", "context_units", "ui_setup", "ui_observation", "cleanup", "recovery", "rediscovery")


def oracle(fixture):
    expected = []
    for case in fixture["scenarios"]:
        for arm in ARMS:
            note_enabled = arm in ("PRIVATE_NOTE", "BOTH")
            ui_enabled = arm in ("ENVIRONMENT_CUE", "BOTH")
            note_exists = note_enabled and any(not x["note"]["omitted"] for x in case["steps"])
            for pos, x in enumerate(case["steps"]):
                charges = dict.fromkeys(COST_KEYS, 0)
                if pos == 0 and note_exists:
                    charges["note_write"] = 2
                if ui_enabled:
                    if pos == 0:
                        charges["ui_setup"] = case["ui_setup"]
                    charges["ui_observation"] = case["ui_observation"]
                    if pos == len(case["steps"]) - 1:
                        if case.get("restore_succeeds", True):
                            charges["cleanup"] = case["ui_cleanup"]
                        else:
                            charges["recovery"] = case["ui_recovery"]
                shared = x["common_fact"] is not None and x["common_fact"] == x["fact"]
                n = x["note"]
                n_present = note_enabled and not n["omitted"]
                n_usable = n_present and n["task"] == x["task"] and n["fact"] == x["fact"] and n["source_version"] == x["fact_version"]
                if n_present and not shared:
                    charges["note_read"] = 1
                    charges["context_units"] = 2
                c = x["cue"]
                c_present = ui_enabled and c["visible"]
                c_usable = c_present and c["task"] == x["task"] and c["fact"] == x["fact"] and c["generation"] == x["app_generation"] and c["adds_info"]
                if shared:
                    origin = "COMMON_OBSERVATION"
                elif n_usable:
                    origin = "PRIVATE_NOTE"
                elif c_usable:
                    origin = "ENVIRONMENT_CUE"
                elif case["rediscovery_succeeds"]:
                    origin = "SAFE_REDISCOVERY"
                    charges["rediscovery"] = case["rediscovery_cost"]
                else:
                    origin = "UNRESOLVED"
                    charges["rediscovery"] = case["rediscovery_cost"]
                visible = not (c_present and c["obscures_warning"])
                restored = not ui_enabled or case.get("restore_succeeds", True)
                expected.append({"case_id": case["id"], "arm": arm, "step_id": x["id"],
                                 "source": origin, "task_correct": origin != "UNRESOLVED",
                                 "warning_visible": visible, "restoration_ok": restored,
                                 "safety_pass": visible and restored, "cost": charges,
                                 "total_cost": sum(charges.values())})
    return expected


def audit(fixture, actual):
    expected = oracle(fixture)
    if len(actual) != len(expected):
        return False, "row_count_mismatch"
    for i, (want, got) in enumerate(zip(expected, actual)):
        if want != got:
            return False, f"row_{i}_mismatch"
    return True, "accepted"


if __name__ == "__main__":
    fixture = json.loads(Path("fixture.json").read_text(encoding="utf-8"))
    candidate = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    ok, reason = audit(fixture, candidate)
    print(json.dumps({"accepted": ok, "reason": reason, "rows": len(candidate)}, sort_keys=True))
    raise SystemExit(0 if ok else 1)
