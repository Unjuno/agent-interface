#!/usr/bin/env python3
"""One-shot raw-source summary candidate for issue #1839 A02."""
import hashlib, json, lzma, sys
from pathlib import Path

SOURCE_SHA = "0d55f782f0e129738b422e52d8066f7fb69a02ebcf2c1691ee711e74a369a740"
KEYS = {f"p{i}-{arm}" for i in (1, 2, 3) for arm in ("attack", "noinput")}


def read(path):
    raw = Path(path).read_bytes()
    if len(raw) != 7392 or hashlib.sha256(raw).hexdigest() != SOURCE_SHA:
        raise ValueError("source_identity")
    data = json.loads(lzma.decompress(raw))
    if set(data) != KEYS:
        raise ValueError("session_inventory")
    return data


def lines(session, key):
    return [json.loads(x) for x in session[key]]


def summarize(key, session):
    events = lines(session, "events_exact_jsonl")
    samples = [x["payload"] for x in lines(session, "scorer_samples_exact_jsonl")]
    if not samples:
        raise ValueError("empty_scorer")
    if any(s.get("schema") != "independent-progress-sample-v2" or
           type(s.get("sample_ns")) is not int or type(s.get("kill_count")) is not int or
           type(s.get("map_exit")) is not bool for s in samples):
        raise ValueError("scorer_types")
    if any(a["sample_ns"] >= b["sample_ns"] for a, b in zip(samples, samples[1:])):
        raise ValueError("scorer_clock")
    baseline = samples[0]["kill_count"]
    locators = []
    for i, s in enumerate(samples[1:], 1):
        if s["kill_count"] > samples[i-1]["kill_count"] and s["kill_count"] > baseline:
            locators.append([key, i, s["sample_ns"], "KILL_COUNT_INCREASE"])
        if s["map_exit"] and not samples[i-1]["map_exit"]:
            locators.append([key, i, s["sample_ns"], "MAP_EXIT"])
    admissions = [e for e in events if e.get("event") == "input_admission"]
    releases = [e for e in events if e.get("event") == "input_release_transition"]
    joined = False
    if key.endswith("-attack"):
        if len(admissions) != 1 or len(releases) != 1:
            raise ValueError("edge_cardinality")
        d = admissions[0]["physical_key_measurement"]
        u = releases[0]["physical_key_measurement"]
        db, ub, de, ue = d["bracket"], u["bracket"], d["adapter_edge"], u["adapter_edge"]
        joined = (db.get("status") == "CONFIRMED_PHYSICAL_DOWN" and ub.get("status") == "CONFIRMED_PHYSICAL_UP"
                  and de.get("edge") == "down" and ue.get("edge") == "up"
                  and de.get("status") == "CONFIRMED_PHYSICAL_DOWN" and ue.get("status") == "CONFIRMED_PHYSICAL_UP"
                  and bool(db.get("press_id")) and bool(ub.get("release_id"))
                  and bool(de.get("actuation_id")) and de.get("actuation_id") == ue.get("actuation_id")
                  and all(db.get(k) == ub.get(k) == de.get(k) == ue.get(k) and bool(db.get(k))
                          for k in ("owner_id", "intent_token", "key"))
                  and de.get("interval") == db.get("physical_down_interval")
                  and ue.get("interval") == ub.get("physical_up_interval"))
        if not joined:
            raise ValueError("physical_join")
    elif admissions or releases:
        raise ValueError("unexpected_input")
    return {"session_id": key, "sample_count": len(samples), "physical_join": joined,
            "endpoint_locators": locators,
            "disposition": "UNRESOLVED_NO_TASK_EFFECT" if not locators else "ENDPOINT_PRESENT_REQUIRES_SEPARATE_CAUSAL_AUDIT",
            "authority_grants": 0}


def main():
    if len(sys.argv) != 3:
        raise SystemExit("usage: candidate.py RAW RESULT")
    data = read(sys.argv[1])
    sessions = [summarize(k, data[k]) for k in sorted(data)]
    result = {"schema": "issue1839-a02-v1", "source_sha256": SOURCE_SHA, "sessions": sessions,
              "attack_joins": sum(x["physical_join"] for x in sessions if x["session_id"].endswith("-attack")),
              "attack_positive_sessions": sum(bool(x["endpoint_locators"]) for x in sessions if x["session_id"].endswith("-attack")),
              "control_positive_sessions": sum(bool(x["endpoint_locators"]) for x in sessions if x["session_id"].endswith("-noinput")),
              "sample_total": sum(x["sample_count"] for x in sessions),
              "authority_grants": sum(x["authority_grants"] for x in sessions)}
    Path(sys.argv[2]).write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k != "sessions"}, sort_keys=True))


if __name__ == "__main__":
    main()
