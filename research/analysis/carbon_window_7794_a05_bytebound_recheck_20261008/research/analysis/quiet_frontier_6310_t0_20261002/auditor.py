import json
import sys


def oracle(row):
    writer_cover = len(row["required_writers"]) == len(row["enrolled_writers"]) and all(w in row["enrolled_writers"] for w in row["required_writers"])
    interval_evidence = writer_cover and row["epoch_ok"] is True and row["sequence_complete"] is True
    if interval_evidence is False:
        verdict = "UNKNOWN"
    elif row["predicate_change_before_F"] is True or row["value_A"] != row["value_F"]:
        verdict = "CHANGE_OBSERVED"
    else:
        verdict = "QUIET_AS_OF_FRONTIER"
    conditional_admission = verdict == "QUIET_AS_OF_FRONTIER" and row["atomic_compare_at_B"] is True and row["version_F"] == row["version_B"]
    return {"case_id": row["id"], "frontier": verdict, "actuation": "ADMIT" if conditional_admission else "BLOCK"}


def verify(fixture, raw):
    expected = {row["id"]: oracle(row) for row in fixture["cases"]}
    assert raw["results"] == expected, "candidate differs from independent raw-fixture oracle"
    assert raw["results"]["change_after_F_before_B"] == {"case_id": "change_after_F_before_B", "frontier": "QUIET_AS_OF_FRONTIER", "actuation": "BLOCK"}
    assert raw["results"]["unregistered_writer"]["frontier"] == "UNKNOWN"
    assert raw["results"]["sequence_gap"]["frontier"] == "UNKNOWN"
    assert raw["results"]["epoch_change"]["frontier"] == "UNKNOWN"
    assert raw["results"]["irrelevant_noise"]["frontier"] == "QUIET_AS_OF_FRONTIER"
    return len(expected)


def main():
    fixture = json.load(open(sys.argv[1], encoding="utf-8"))
    raw = json.load(open(sys.argv[2], encoding="utf-8"))
    count = verify(fixture, raw)
    mutations = []
    changed = json.loads(json.dumps(raw)); changed["results"]["change_after_F_before_B"]["actuation"] = "ADMIT"
    mutations.append(changed)
    missing = json.loads(json.dumps(raw)); del missing["results"]["sequence_gap"]
    mutations.append(missing)
    forged = json.loads(json.dumps(raw)); forged["results"]["unregistered_writer"]["frontier"] = "QUIET_AS_OF_FRONTIER"
    mutations.append(forged)
    false_change = json.loads(json.dumps(raw)); false_change["results"]["change_before_F"]["frontier"] = "QUIET_AS_OF_FRONTIER"
    mutations.append(false_change)
    rejects = 0
    for mutant in mutations:
        try:
            verify(fixture, mutant)
        except (AssertionError, KeyError, TypeError):
            rejects += 1
    assert rejects == 4, "one or more frozen mutations escaped"
    print(json.dumps({"schema": "6310-audit-v1", "cases": count, "errors": 0, "mutations_rejected": rejects}, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
