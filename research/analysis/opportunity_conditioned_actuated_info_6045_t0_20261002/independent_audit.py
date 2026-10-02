"""Raw-only auditor; implements its own finite enumerator, no candidate imports."""
import hashlib
import json
from pathlib import Path


def interval_of(event, point, bounded):
    value = event.get(bounded)
    return (value[0], value[1]) if value is not None else (event[point], event[point])


def expected(event, censor_time):
    clocks_ok = event.get("clock_comparable", True) is True
    delivery_rows = []
    for observation in event["observations"]:
        source_start, source_end = interval_of(observation, "generation", "generation_interval")
        receipt_start, receipt_end = interval_of(observation, "delivery", "delivery_interval")
        chronology_proved = clocks_ok and source_end < receipt_start
        age_bounds = [receipt_start - source_end, receipt_end - source_start] if chronology_proved else None
        exact_age = age_bounds[0] if age_bounds is not None and age_bounds[0] == age_bounds[1] else None
        delivery_rows.append({"observation_id": observation["id"], "delivery_age": exact_age,
                              "delivery_age_interval": age_bounds,
                              "clock_status": "COMPARABLE" if chronology_proved else "HOLD_UNORDERED_LINEAGE"})

    observed_effect = event["effect"]
    belongs_to_opportunity = (observed_effect is not None and observed_effect["relevant"] is True and
                              observed_effect["opportunity_id"] == event.get("opportunity_id", event["id"].replace("_", "-")))
    if event["eligible"] is not True or event["needs_intervention"] is not True:
        classification = "NOT_APPLICABLE"
    elif belongs_to_opportunity and (not clocks_ok or observed_effect["clock_ordered"] is not True):
        classification = "UNKNOWN_CLOCK_RELATION"
    elif belongs_to_opportunity:
        effect_start, effect_end = interval_of(observed_effect, "time", "time_interval")
        if effect_end <= event["deadline"]:
            classification = "RELEVANT_EFFECT_ON_TIME"
        elif effect_start > event["deadline"]:
            classification = "RELEVANT_EFFECT_LATE"
        else:
            classification = "UNKNOWN_CLOCK_RELATION"
    elif censor_time >= event["deadline"]:
        classification = "MISSED_NO_RELEVANT_EFFECT"
    else:
        classification = "UNKNOWN_NO_RELEVANT_EFFECT"

    source_age = None
    source_age_bounds = None
    age_status = "NO_RELEVANT_EFFECT"
    if event["eligible"] is not True or event["needs_intervention"] is not True:
        age_status = "NOT_APPLICABLE"
    elif belongs_to_opportunity:
        if not clocks_ok or observed_effect["clock_ordered"] is not True:
            age_status = "HOLD_UNORDERED_LINEAGE"
        elif observed_effect["lineage_proven"] is not True or len(observed_effect["lineage"]) != 1:
            age_status = "HOLD_CAUSAL_ANCESTOR_UNKNOWN"
        else:
            source_record = next((o for o in event["observations"] if o["id"] == observed_effect["lineage"][0]), None)
            if source_record is None:
                age_status = "HOLD_LINEAGE_SOURCE_MISSING"
            else:
                source_start, source_end = interval_of(source_record, "generation", "generation_interval")
                effect_start, effect_end = interval_of(observed_effect, "time", "time_interval")
                if source_end >= effect_start:
                    age_status = "HOLD_UNORDERED_LINEAGE"
                else:
                    age_status = "SINGLE_PROVEN_SOURCE"
                    source_age_bounds = [effect_start - source_end, effect_end - source_start]
                    if source_age_bounds[0] == source_age_bounds[1]:
                        source_age = source_age_bounds[0]
    else:
        source_record = None

    if belongs_to_opportunity and age_status == "SINGLE_PROVEN_SOURCE":
        source_record = next(o for o in event["observations"] if o["id"] == observed_effect["lineage"][0])
    else:
        source_record = None
    onset_age = None
    onset_bounds = None
    if belongs_to_opportunity and clocks_ok and event["onset"] is not None:
        effect_start, effect_end = interval_of(observed_effect, "time", "time_interval")
        if event["onset"] < effect_start:
            onset_bounds = [effect_start - event["onset"], effect_end - event["onset"]]
            if onset_bounds[0] == onset_bounds[1]:
                onset_age = onset_bounds[0]

    return {"events": event, "id": event["id"], "delivery_ages": delivery_rows,
            "opportunity_outcome": classification, "onset_to_effect": onset_age,
            "onset_to_effect_interval": onset_bounds, "source_effect_age": source_age,
            "source_effect_age_interval": source_age_bounds,
            "source_effect_age_status": age_status,
            "source_validity": source_record["validity"] if source_record else None,
            "relevant_effect_reset": bool(belongs_to_opportunity)}


def audit(fixture_bytes, ledger_bytes, manifest_bytes):
    issues = []
    try:
        fixture = json.loads(fixture_bytes)
        manifest = json.loads(manifest_bytes)
        actual = [json.loads(line) for line in ledger_bytes.splitlines()]
    except (ValueError, TypeError) as error:
        return [f"invalid JSON: {error}"]
    if manifest.get("allocation") != fixture.get("allocation"):
        issues.append("allocation mismatch")
    if manifest.get("fixture_sha256") != hashlib.sha256(fixture_bytes).hexdigest():
        issues.append("fixture hash mismatch")
    if manifest.get("ledger_sha256") != hashlib.sha256(ledger_bytes).hexdigest():
        issues.append("ledger hash mismatch")
    files = ("candidate.py", "run_candidate.py", "independent_audit.py")
    source_identity = {name: hashlib.sha256((Path(__file__).parent / name).read_bytes()).hexdigest() for name in files}
    if manifest.get("source_sha256") != source_identity:
        issues.append("source hashes mismatch")
    wanted = [expected({**row, "end_time": fixture["end_time"]}, fixture["end_time"]) for row in fixture.get("rows", [])]
    if len(actual) != len(wanted) or manifest.get("row_count") != len(wanted):
        issues.append("incomplete ledger")
    if [row.get("id") for row in actual] != [row["id"] for row in wanted]:
        issues.append("case identity/order mismatch")
    if actual != wanted:
        issues.append("derived ledger differs from independent reconstruction")
    return issues


def main():
    import sys
    if len(sys.argv) != 4:
        raise SystemExit("usage: independent_audit.py FIXTURE LEDGER MANIFEST")
    errors = audit(*(Path(path).read_bytes() for path in sys.argv[1:]))
    print(json.dumps({"status": "PASS_METHOD_SCOPED" if not errors else "FAIL_METHOD", "errors": errors}, sort_keys=True))
    raise SystemExit(0 if not errors else 1)


if __name__ == "__main__":
    main()
