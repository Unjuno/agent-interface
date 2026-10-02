#!/usr/bin/env python3
"""Source-only classifier for the frozen #4193 retained corpus; no authority."""
import hashlib
import json
import lzma
import sys
from pathlib import Path

EXPECTED_SHA = "0d55f782f0e129738b422e52d8066f7fb69a02ebcf2c1691ee711e74a369a740"
EXPECTED_KEYS = {f"p{p}-{arm}" for p in (1, 2, 3) for arm in ("attack", "noinput")}


def decode(path):
    raw = Path(path).read_bytes()
    if len(raw) != 7392 or hashlib.sha256(raw).hexdigest() != EXPECTED_SHA:
        raise ValueError("frozen source identity mismatch")
    data = json.loads(lzma.decompress(raw))
    if set(data) != EXPECTED_KEYS:
        raise ValueError("frozen session inventory mismatch")
    return data


def rows(session, field):
    return [json.loads(line) for line in session[field]]


def classify(session_id, session):
    events = rows(session, "events_exact_jsonl")
    samples = [row["payload"] for row in rows(session, "scorer_samples_exact_jsonl")]
    if not samples or any(s.get("schema") != "independent-progress-sample-v2" for s in samples):
        raise ValueError(f"{session_id}: scorer schema")
    for s in samples:
        if type(s.get("sample_ns")) is not int or type(s.get("kill_count")) is not int or type(s.get("map_exit")) is not bool:
            raise ValueError(f"{session_id}: scorer field type")
    stamps = [s["sample_ns"] for s in samples]
    if any(a >= b for a, b in zip(stamps, stamps[1:])):
        raise ValueError(f"{session_id}: nonmonotonic scorer clock")
    endpoints = []
    baseline = samples[0]["kill_count"]
    was_exit = samples[0]["map_exit"]
    for i, sample in enumerate(samples[1:], 1):
        if sample["kill_count"] > baseline:
            endpoints.append([session_id, i, sample["sample_ns"], "KILL_COUNT_INCREASE"])
        if sample["map_exit"] and not was_exit:
            endpoints.append([session_id, i, sample["sample_ns"], "MAP_EXIT"])
        was_exit = sample["map_exit"]
    admission = [e for e in events if e.get("event") == "input_admission"]
    release = [e for e in events if e.get("event") == "input_release_transition"]
    joined = False
    if session_id.endswith("-attack"):
        if len(admission) != 1 or len(release) != 1:
            raise ValueError(f"{session_id}: edge cardinality")
        down = admission[0]["physical_key_measurement"]
        up = release[0]["physical_key_measurement"]
        db, ub = down["bracket"], up["bracket"]
        de, ue = down["adapter_edge"], up["adapter_edge"]
        joined = (
            db.get("status") == "CONFIRMED_PHYSICAL_DOWN"
            and ub.get("status") == "CONFIRMED_PHYSICAL_UP"
            and de.get("status") == "CONFIRMED_PHYSICAL_DOWN"
            and ue.get("status") == "CONFIRMED_PHYSICAL_UP"
            and bool(db.get("press_id")) and bool(ub.get("release_id"))
            and de.get("actuation_id") not in (None, "")
            and de.get("actuation_id") == ue.get("actuation_id")
            and db.get("owner_id") == ub.get("owner_id") == de.get("owner_id") == ue.get("owner_id")
            and db.get("intent_token") == ub.get("intent_token") == de.get("intent_token") == ue.get("intent_token")
            and db.get("key") == ub.get("key") == de.get("key") == ue.get("key")
            and de.get("interval") == db.get("physical_down_interval")
            and ue.get("interval") == ub.get("physical_up_interval")
        )
        if not joined:
            raise ValueError(f"{session_id}: physical edge join")
    elif admission or release:
        raise ValueError(f"{session_id}: unexpected input edge")
    return {"session_id": session_id, "sample_count": len(samples), "physical_join": joined,
            "endpoint_locators": endpoints, "disposition": "UNRESOLVED_NO_TASK_EFFECT" if not endpoints else "ENDPOINT_PRESENT_REQUIRES_SEPARATE_CAUSAL_AUDIT",
            "authority_grants": 0}


def main():
    if len(sys.argv) != 3:
        raise SystemExit("usage: candidate.py RAW RESULT")
    data = decode(sys.argv[1])
    sessions = [classify(key, data[key]) for key in sorted(data)]
    result = {"schema": "issue1839-source-bound-a01-v1", "source_sha256": EXPECTED_SHA,
              "sessions": sessions, "attack_joins": sum(x["physical_join"] for x in sessions if x["session_id"].endswith("-attack")),
              "attack_endpoint_sessions": sum(bool(x["endpoint_locators"]) for x in sessions if x["session_id"].endswith("-attack")),
              "control_endpoint_sessions": sum(bool(x["endpoint_locators"]) for x in sessions if x["session_id"].endswith("-noinput")),
              "sample_total": sum(x["sample_count"] for x in sessions), "authority_grants": sum(x["authority_grants"] for x in sessions)}
    Path(sys.argv[2]).write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k != "sessions"}, sort_keys=True))


if __name__ == "__main__":
    main()
