#!/usr/bin/env python3
"""Independent raw-only verifier for the #4193 v3 compatibility record."""
import hashlib
import json
import lzma
import sys
from pathlib import Path

EXPECTED = "0d55f782f0e129738b422e52d8066f7fb69a02ebcf2c1691ee711e74a369a740"
KEYS = {
    "p1-attack", "p1-noinput", "p2-attack", "p2-noinput",
    "p3-attack", "p3-noinput",
}


def decode(path):
    raw = Path(path).read_bytes()
    if hashlib.sha256(raw).hexdigest() != EXPECTED:
        raise SystemExit("AUDIT_FAIL source digest")
    decoded = json.loads(lzma.decompress(raw))
    if set(decoded) != KEYS:
        raise SystemExit("AUDIT_FAIL session set")
    return decoded


def verify_session(key, value, recorded):
    events = [json.loads(row) for row in value["events_exact_jsonl"]]
    samples = [json.loads(row)["payload"] for row in value["scorer_samples_exact_jsonl"]]
    assert recorded["session_key"] == key
    assert recorded["sample_count"] == len(samples) > 0
    assert all(s["schema"] == "independent-progress-sample-v2" for s in samples)
    stamps = [s["sample_ns"] for s in samples]
    assert all(a < b for a, b in zip(stamps, stamps[1:]))
    assert recorded["sample_ns_strictly_increasing_within_session"] is True
    assert recorded["all_kill_count_zero"] == all(s["kill_count"] == 0 for s in samples)
    assert recorded["any_map_exit"] == any(bool(s["map_exit"]) for s in samples)
    baseline = samples[0]["kill_count"]
    prior_exit = bool(samples[0]["map_exit"])
    locators = []
    for index, sample in enumerate(samples):
        if sample["kill_count"] > baseline:
            locators.append([key, index, sample["sample_ns"], "KILL_COUNT_INCREASE"])
        now_exit = bool(sample["map_exit"])
        if now_exit and not prior_exit:
            locators.append([key, index, sample["sample_ns"], "MAP_EXIT"])
        prior_exit = now_exit
    assert recorded["positive_endpoint_count"] == len(locators)
    assert [item["locator"] for item in recorded["positive_endpoints"]] == locators
    assert recorded["native_source_event_id_present"] == any("source_event_id" in e for e in events)
    assert recorded["native_scorer_event_id_present"] == any("scorer_event_id" in e for e in events)

    if key.endswith("-attack"):
        down_events = [e for e in events if e.get("event") == "input_admission"]
        up_events = [e for e in events if e.get("event") == "input_release_transition"]
        assert len(down_events) == len(up_events) == 1
        dm = down_events[0]["physical_key_measurement"]
        um = up_events[0]["physical_key_measurement"]
        db, ub = dm["bracket"], um["bracket"]
        de, ue = dm["adapter_edge"], um["adapter_edge"]
        expected = {
            "down_confirmed": db["status"] == "CONFIRMED_PHYSICAL_DOWN",
            "up_confirmed": ub["status"] == "CONFIRMED_PHYSICAL_UP",
            "press_id_present": bool(db.get("press_id")),
            "release_id_present": bool(ub.get("release_id")),
            "actuation_id_equal": de["actuation_id"] == ue["actuation_id"],
            "owner_id_equal": db["owner_id"] == ub["owner_id"] == de["owner_id"] == ue["owner_id"],
            "intent_token_equal": db["intent_token"] == ub["intent_token"] == de["intent_token"] == ue["intent_token"],
            "key_equal": db["key"] == ub["key"] == de["key"] == ue["key"],
            "down_edge_matches_bracket": de["interval"] == db["physical_down_interval"],
            "up_edge_matches_bracket": ue["interval"] == ub["physical_up_interval"],
        }
        assert recorded["physical_receipt_checks"] == expected
        assert recorded["physical_receipt_join_supported"] is all(expected.values())
        ids = recorded["native_receipt_ids"]
        assert ids == {
            "press_id": db["press_id"], "release_id": ub["release_id"],
            "actuation_id": de["actuation_id"], "owner_id": db["owner_id"],
            "intent_token": db["intent_token"], "key": db["key"],
        }
    else:
        assert recorded["physical_receipt_join_supported"] is None
        assert not any(e.get("event") in {"input_admission", "input_release_transition"} for e in events)


def main():
    if len(sys.argv) != 3:
        raise SystemExit("usage: audit.py RAW_USED.json.xz RESULT.json")
    data = decode(sys.argv[1])
    result = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
    by_key = {s["session_key"]: s for s in result["sessions"]}
    assert set(by_key) == KEYS
    for key, value in data.items():
        verify_session(key, value, by_key[key])
    attacks = [by_key[k] for k in sorted(KEYS) if k.endswith("-attack")]
    controls = [by_key[k] for k in sorted(KEYS) if k.endswith("-noinput")]
    assert result["source_sha256"] == EXPECTED
    assert result["session_count"] == 6
    assert result["attack_physical_joins_supported"] == sum(s["physical_receipt_join_supported"] for s in attacks) == 3
    assert result["attack_sessions_with_positive_scorer_endpoint"] == sum(s["positive_endpoint_count"] > 0 for s in attacks) == 0
    assert result["noinput_sessions_with_positive_scorer_endpoint"] == sum(s["positive_endpoint_count"] > 0 for s in controls) == 0
    assert result["attack_positive_endpoint_total"] == sum(s["positive_endpoint_count"] for s in attacks) == 0
    assert result["noinput_positive_endpoint_total"] == sum(s["positive_endpoint_count"] for s in controls) == 0
    assert result["scorer_sample_total"] == sum(s["sample_count"] for s in by_key.values()) == 196
    assert result["native_source_event_id_present_anywhere"] is False
    assert result["native_scorer_event_id_present_anywhere"] is False
    assert result["disposition"] == "HOLD_NO_POSITIVE_SCORER_EVENT"
    print("AUDIT_PASS sessions=6 physical_joins=3/3 attack_positive_sessions=0/3 noinput_positive_sessions=0/3 scorer_samples=196 source_event_ids=absent scorer_event_ids=absent")


if __name__ == "__main__":
    main()
