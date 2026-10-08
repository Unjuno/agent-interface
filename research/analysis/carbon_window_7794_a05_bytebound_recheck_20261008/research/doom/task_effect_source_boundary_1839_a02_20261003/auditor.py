#!/usr/bin/env python3
"""Independent raw-only A02 auditor; deliberately does not import candidate.py."""
import copy, hashlib, json, lzma, sys
from pathlib import Path

RAW_SHA = "0d55f782f0e129738b422e52d8066f7fb69a02ebcf2c1691ee711e74a369a740"
INVENTORY = {f"p{i}-{arm}" for i in (1, 2, 3) for arm in ("attack", "noinput")}


def raw_sessions(path):
    blob = Path(path).read_bytes()
    assert len(blob) == 7392 and hashlib.sha256(blob).hexdigest() == RAW_SHA
    parsed = json.loads(lzma.decompress(blob))
    assert set(parsed) == INVENTORY
    return parsed


def objects(record, field):
    return [json.loads(line) for line in record[field]]


def derive_endpoint_locators(session, payloads):
    found = []
    for i in range(1, len(payloads)):
        before, current = payloads[i-1], payloads[i]
        if current["kill_count"] > before["kill_count"] and current["kill_count"] > payloads[0]["kill_count"]:
            found.append([session, i, current["sample_ns"], "KILL_COUNT_INCREASE"])
        if current["map_exit"] and not before["map_exit"]:
            found.append([session, i, current["sample_ns"], "MAP_EXIT"])
    return found


def physical_pair_ok(key, events):
    down = [e for e in events if e.get("event") == "input_admission"]
    up = [e for e in events if e.get("event") == "input_release_transition"]
    if key.endswith("-noinput"):
        return not down and not up
    if len(down) != 1 or len(up) != 1:
        return False
    da = down[0]["physical_key_measurement"]
    ua = up[0]["physical_key_measurement"]
    db, ub, de, ue = da["bracket"], ua["bracket"], da["adapter_edge"], ua["adapter_edge"]
    if db.get("status") != "CONFIRMED_PHYSICAL_DOWN" or ub.get("status") != "CONFIRMED_PHYSICAL_UP":
        return False
    if (de.get("edge"), de.get("status")) != ("down", "CONFIRMED_PHYSICAL_DOWN"):
        return False
    if (ue.get("edge"), ue.get("status")) != ("up", "CONFIRMED_PHYSICAL_UP"):
        return False
    ids = (db.get("press_id"), ub.get("release_id"), de.get("actuation_id"), ue.get("actuation_id"))
    if not all(ids) or ids[2] != ids[3]:
        return False
    for field in ("owner_id", "intent_token", "key"):
        values = (db.get(field), ub.get(field), de.get(field), ue.get(field))
        if not values[0] or len(set(values)) != 1:
            return False
    return de.get("interval") == db.get("physical_down_interval") and ue.get("interval") == ub.get("physical_up_interval")


def reconstruct(data):
    records = []
    for key in sorted(data):
        session = data[key]
        samples = [x["payload"] for x in objects(session, "scorer_samples_exact_jsonl")]
        events = objects(session, "events_exact_jsonl")
        assert samples
        assert all(s.get("schema") == "independent-progress-sample-v2" for s in samples)
        assert all(type(s.get("sample_ns")) is int and type(s.get("kill_count")) is int and type(s.get("map_exit")) is bool for s in samples)
        assert all(a["sample_ns"] < b["sample_ns"] for a, b in zip(samples, samples[1:]))
        assert physical_pair_ok(key, events)
        locators = derive_endpoint_locators(key, samples)
        records.append({"session_id": key, "sample_count": len(samples),
                        "physical_join": key.endswith("-attack"), "endpoint_locators": locators,
                        "disposition": "UNRESOLVED_NO_TASK_EFFECT" if not locators else "ENDPOINT_PRESENT_REQUIRES_SEPARATE_CAUSAL_AUDIT",
                        "authority_grants": 0})
    return {"schema": "issue1839-a02-v1", "source_sha256": RAW_SHA, "sessions": records,
            "attack_joins": sum(x["physical_join"] for x in records if x["session_id"].endswith("-attack")),
            "attack_positive_sessions": sum(bool(x["endpoint_locators"]) for x in records if x["session_id"].endswith("-attack")),
            "control_positive_sessions": sum(bool(x["endpoint_locators"]) for x in records if x["session_id"].endswith("-noinput")),
            "sample_total": sum(x["sample_count"] for x in records),
            "authority_grants": sum(x["authority_grants"] for x in records)}


def corruption_cases(candidate):
    cases = {}
    c = copy.deepcopy(candidate); c["sessions"].pop(); cases["drop_session"] = c
    c = copy.deepcopy(candidate); c["sessions"].append(copy.deepcopy(c["sessions"][0])); cases["duplicate_session"] = c
    c = copy.deepcopy(candidate); c["sessions"][0]["endpoint_locators"] = [["p1-attack", 1, 0, "MAP_EXIT"]]; cases["forge_effect"] = c
    c = copy.deepcopy(candidate); next(x for x in c["sessions"] if x["session_id"] == "p1-attack")["physical_join"] = False; cases["erase_physical_join"] = c
    c = copy.deepcopy(candidate); c["sample_total"] += 1; cases["alter_sample_count"] = c
    c = copy.deepcopy(candidate); c["authority_grants"] = 1; cases["grant_authority"] = c
    return cases


def check_summary(observed, expected):
    for field, value in expected.items():
        assert observed.get(field) == value, f"field:{field}"
    assert set(observed) == set(expected), "summary_field_set"


def main():
    if len(sys.argv) != 4:
        raise SystemExit("usage: auditor.py RAW CANDIDATE AUDIT")
    expected = reconstruct(raw_sessions(sys.argv[1]))
    supplied = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
    check_summary(supplied, expected)
    rejected = {}
    for label, mutant in corruption_cases(supplied).items():
        try:
            check_summary(mutant, expected)
        except AssertionError:
            rejected[label] = True
        else:
            rejected[label] = False
    assert len(rejected) == 6 and all(rejected.values())
    assert expected["attack_joins"] == 3 and expected["sample_total"] == 194
    assert expected["attack_positive_sessions"] == expected["control_positive_sessions"] == 0
    result = {"status": "PASS_AUDIT_MUTATION_CONTRACT_SCOPED", "candidate_matches_raw_oracle": True,
              "sessions": 6, "attack_physical_joins": 3, "scorer_samples": 194,
              "attack_positive_sessions": 0, "noinput_positive_sessions": 0, "authority_grants": 0,
              "corruptions_rejected": rejected,
              "scope": "offline retained-source and audit-mutation qualification only; no task-effect sensitivity or live/gameplay claim"}
    Path(sys.argv[3]).write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
