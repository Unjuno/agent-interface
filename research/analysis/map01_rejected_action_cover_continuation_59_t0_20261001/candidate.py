"""Finite model of independent cover-contract admission; never dispatches input."""
import json
import argparse
from pathlib import Path


def evaluate(source_health, current_health, action_max_loss, cover_max_loss,
             cover_critical_minimum, evidence_age_ms, max_evidence_age_ms,
             source_matches):
    observed = type(current_health) is int and current_health >= 0
    source_valid = type(source_health) is int and source_health >= 0
    age_valid = (type(evidence_age_ms) is int and evidence_age_ms >= 0 and
                 type(max_evidence_age_ms) is int and max_evidence_age_ms >= 0 and
                 evidence_age_ms <= max_evidence_age_ms)
    caps_valid = all(type(value) is int and value >= 0 for value in
                     (action_max_loss, cover_max_loss, cover_critical_minimum))
    identity_valid = source_matches is True

    action_floor = max(35, source_health - action_max_loss) if source_valid and caps_valid else None
    action_admitted = (observed and source_valid and caps_valid and age_valid and
                       identity_valid and current_health >= action_floor)

    cover_floor = max(cover_critical_minimum,
                      source_health - cover_max_loss) if source_valid and caps_valid else None
    cover_admitted = (observed and source_valid and caps_valid and age_valid and
                      identity_valid and current_health >= cover_floor)
    return {
        "action": "ADMIT" if action_admitted else "REJECT",
        "action_floor": action_floor,
        "cover": "ADMIT_BOUNDED_CONTINUATION" if cover_admitted else "REJECT",
        "cover_floor": cover_floor,
        "input_authority": False,
    }


def rows():
    cases = [
        ("retained_boundary", 97, 85, 8, 12, 25, 0, 30000, True),
        ("one_below_floor", 97, 84, 8, 12, 25, 0, 30000, True),
        ("one_above_floor", 97, 86, 8, 12, 25, 0, 30000, True),
        ("missing_health", 97, None, 8, 12, 25, 0, 30000, True),
        ("stale_evidence", 97, 85, 8, 12, 25, 30001, 30000, True),
        ("mismatched_source", 97, 85, 8, 12, 25, 0, 30000, False),
    ]
    return [{"case": name, **evaluate(*values)} for name, *values in cases]


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path,
                        default=Path(__file__).with_name("candidate_output.json"))
    destination = parser.parse_args().output
    destination.write_text(json.dumps({"rows": rows()}, indent=2) + "\n")
