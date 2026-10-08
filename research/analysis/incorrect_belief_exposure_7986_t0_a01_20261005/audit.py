"""Independent truth-side adjudicator; does not import the candidate implementation."""

import hashlib
import json
import sys
from pathlib import Path


def adjudicate(fixture, raw, frozen_digest=None):
    errors = []
    canonical = json.dumps(fixture, sort_keys=True, separators=(",", ":")).encode()
    actual_digest = hashlib.sha256(canonical).hexdigest()
    if frozen_digest is not None and actual_digest != frozen_digest:
        errors.append("truth_fixture_hash_mismatch")
    rows = {row["case_id"]: row for row in fixture["candidate_view"]}
    truth = {row["case_id"]: row for row in fixture["truth_sidecar"]}
    if set(rows) != set(truth) or set(rows) != set(raw):
        errors.append("case_id_set_mismatch")
    result = {}
    for case_id, row in rows.items():
        label = truth.get(case_id, {})
        expected_age = row["end_tick"] - row["capture_tick"]
        expected_effect_ages = [event["tick"] - row["capture_tick"] for event in row["effects"]]
        observation = raw.get(case_id, {})
        if observation.get("observation_age_ticks") != expected_age or observation.get("effect_ages_ticks") != expected_effect_ages:
            errors.append(f"{case_id}:candidate_observation_mismatch")
        if observation.get("effects") != [{"tick": event["tick"], "action": event["action"]} for event in row["effects"]]:
            errors.append(f"{case_id}:effect_event_mismatch")
        if not label.get("truth_known") or not label.get("clock_order_known"):
            clocks_known = label.get("clock_order_known", False)
            result[case_id] = {
                "status": "UNKNOWN", "observation_age_ticks": expected_age if clocks_known else None,
                "belief_error_ticks": None, "unsafe_admissibility_ticks": None,
                "realized_unsafe_effects": None, "effect_ages_ticks": expected_effect_ages if clocks_known else None,
            }
            continue
        if row["end_tick"] < row["start_tick"]:
            errors.append(f"{case_id}:negative_interval")
            duration = 0
        else:
            duration = row["end_tick"] - row["start_tick"]
        governed = row["authority_active"] and row["belief_active"]
        belief_error = duration if governed and label["truth_state"] not in row["belief_states"] else 0
        forbidden_admitted = set(row["admitted_actions"]) & set(label["truth_forbidden_actions"])
        exposure = duration if governed and row["action_available"] and forbidden_admitted else 0
        unsafe_effects = sum(
            1 for event in row["effects"]
            if event["action"] in label["truth_forbidden_actions"]
            and row["start_tick"] <= event["tick"] < row["end_tick"]
        )
        result[case_id] = {
            "status": "KNOWN", "observation_age_ticks": expected_age,
            "belief_error_ticks": belief_error, "unsafe_admissibility_ticks": exposure,
            "realized_unsafe_effects": unsafe_effects, "effect_ages_ticks": expected_effect_ages,
        }
    return {"passed": not errors, "errors": errors, "cases": result}


def main():
    fixture = json.loads(Path(sys.argv[1]).read_text())
    raw = json.loads(Path(sys.argv[2]).read_text())
    freeze = json.loads(Path(sys.argv[4]).read_text())
    result = adjudicate(fixture, raw, freeze["fixture_canonical_sha256"])
    Path(sys.argv[3]).write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(json.dumps({"passed": result["passed"], "errors": result["errors"], "case_count": len(result["cases"])}))
    raise SystemExit(0 if result["passed"] else 1)


if __name__ == "__main__":
    main()
