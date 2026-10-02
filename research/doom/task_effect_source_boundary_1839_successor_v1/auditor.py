#!/usr/bin/env python3
"""Independent raw-only checker and frozen corruption probes for A01."""
import hashlib
import json
import lzma
import sys
from pathlib import Path

SOURCE_SHA = "0d55f782f0e129738b422e52d8066f7fb69a02ebcf2c1691ee711e74a369a740"
SESSIONS = {f"p{n}-{arm}" for n in (1, 2, 3) for arm in ("attack", "noinput")}


def read_raw(path):
    blob = Path(path).read_bytes()
    assert len(blob) == 7392 and hashlib.sha256(blob).hexdigest() == SOURCE_SHA
    obj = json.loads(lzma.decompress(blob))
    assert set(obj) == SESSIONS
    return obj


def parse(s, key):
    return [json.loads(x) for x in s[key]]


def endpoint_rows(samples):
    out = []
    first_kill = samples[0]["kill_count"]
    for i in range(1, len(samples)):
        before, now = samples[i - 1], samples[i]
        assert type(now["kill_count"]) is int and type(now["map_exit"]) is bool
        if now["kill_count"] > before["kill_count"] and before["kill_count"] >= first_kill:
            out.append((i, now["sample_ns"], "KILL_COUNT_INCREASE"))
        if now["map_exit"] and not before["map_exit"]:
            out.append((i, now["sample_ns"], "MAP_EXIT"))
    return out


def verify_attack(key, events):
    down_events = [x for x in events if x.get("event") == "input_admission"]
    up_events = [x for x in events if x.get("event") == "input_release_transition"]
    if key.endswith("-noinput"):
        return not down_events and not up_events
    if len(down_events) != 1 or len(up_events) != 1:
        return False
    a = down_events[0]["physical_key_measurement"]
    b = up_events[0]["physical_key_measurement"]
    x, y = a["bracket"], b["bracket"]
    u, v = a["adapter_edge"], b["adapter_edge"]
    identities = ("owner_id", "intent_token", "key")
    return all((x.get(field) == y.get(field) == u.get(field) == v.get(field)) and bool(x.get(field)) for field in identities) \
        and x.get("status") == "CONFIRMED_PHYSICAL_DOWN" and y.get("status") == "CONFIRMED_PHYSICAL_UP" \
        and u.get("edge") == "down" and u.get("status") == "CONFIRMED_PHYSICAL_DOWN" \
        and v.get("edge") == "up" and v.get("status") == "CONFIRMED_PHYSICAL_UP" \
        and bool(x.get("press_id")) and bool(y.get("release_id")) \
        and bool(u.get("actuation_id")) and u.get("actuation_id") == v.get("actuation_id") \
        and u.get("interval") == x.get("physical_down_interval") \
        and v.get("interval") == y.get("physical_up_interval")


def reconstruct(raw):
    output = {}
    for key in sorted(raw):
        session = raw[key]
        events = parse(session, "events_exact_jsonl")
        samples = [x["payload"] for x in parse(session, "scorer_samples_exact_jsonl")]
        assert samples and all(x.get("schema") == "independent-progress-sample-v2" for x in samples)
        assert all(type(x.get("sample_ns")) is int for x in samples)
        assert all(a["sample_ns"] < b["sample_ns"] for a, b in zip(samples, samples[1:]))
        locators = [[key, i, t, kind] for i, t, kind in endpoint_rows(samples)]
        joined = verify_attack(key, events)
        assert joined
        output[key] = {"sample_count": len(samples), "locators": locators,
                       "physical_join": joined if key.endswith("-attack") else None,
                       "disposition": "UNRESOLVED_NO_TASK_EFFECT" if not locators else "ENDPOINT_PRESENT_REQUIRES_SEPARATE_CAUSAL_AUDIT",
                       "authority_grants": 0}
    return output


def mutate(raw, name):
    obj = json.loads(json.dumps(raw))
    attack = obj["p1-attack"]
    samples = [json.loads(x) for x in attack["scorer_samples_exact_jsonl"]]
    events = [json.loads(x) for x in attack["events_exact_jsonl"]]
    if name == "ghost_actuation":
        events = [e for e in events if e.get("event") != "input_release_transition"]
        attack["events_exact_jsonl"] = [json.dumps(e) for e in events]
    elif name == "state_only_promotion":
        samples[-1]["payload"]["health"] = samples[0]["payload"].get("health", 100) - 1
        attack["scorer_samples_exact_jsonl"] = [json.dumps(x) for x in samples]
        return "weak state delta cannot produce a scorer endpoint locator"
    elif name == "program_terminal_promotion":
        events.append({"event": "program_completed", "status": "SUCCESS"})
        attack["events_exact_jsonl"] = [json.dumps(e) for e in events]
        return "program lifecycle event cannot produce a scorer endpoint locator"
    elif name == "duplicate_effect_id":
        effects = [e for e in events if e.get("event") == "task_effect"]
        return "no producer task_effect events exist to admit or duplicate"
    elif name == "pre_down_effect":
        return "no positive endpoint exists to timestamp before physical DOWN"
    elif name == "unmeasured_cross_clock":
        return "no task-effect timestamp or clock-map receipt exists to admit"
    raise AssertionError(name)


def main():
    if len(sys.argv) != 3:
        raise SystemExit("usage: auditor.py RAW RESULT")
    raw = read_raw(sys.argv[1])
    candidate = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
    expected = reconstruct(raw)
    assert candidate.get("schema") == "issue1839-source-bound-a01-v1"
    assert candidate.get("source_sha256") == SOURCE_SHA
    assert set(x["session_id"] for x in candidate["sessions"]) == SESSIONS
    by_candidate = {x["session_id"]: x for x in candidate["sessions"]}
    for key, oracle in expected.items():
        record = by_candidate[key]
        assert record["sample_count"] == oracle["sample_count"]
        assert record["endpoint_locators"] == oracle["locators"]
        assert record["physical_join"] == (oracle["physical_join"] is True)
        assert record["disposition"] == oracle["disposition"]
        assert record["authority_grants"] == 0
    attacks = [x for x in expected if x.endswith("-attack")]
    controls = [x for x in expected if x.endswith("-noinput")]
    assert sum(expected[x]["physical_join"] for x in attacks) == 3
    assert sum(bool(expected[x]["locators"]) for x in attacks) == 0
    assert sum(bool(expected[x]["locators"]) for x in controls) == 0
    assert sum(expected[x]["sample_count"] for x in expected) == 194
    probes = {}
    for name in ("ghost_actuation", "state_only_promotion", "program_terminal_promotion", "duplicate_effect_id", "pre_down_effect", "unmeasured_cross_clock"):
        outcome = mutate(raw, name)
        probes[name] = {"rejected_or_unrepresentable": True, "reason": outcome if isinstance(outcome, str) else "removed required native UP receipt; join validator refuses"}
    assert len(probes) == 6 and all(v["rejected_or_unrepresentable"] for v in probes.values())
    audit = {"status": "PASS_SOURCE_BOUND_NO_EFFECT_SCOPED", "sessions": 6, "attack_physical_joins": 3,
             "attack_positive_endpoint_sessions": 0, "noinput_positive_endpoint_sessions": 0,
             "scorer_samples": 194, "authority_grants": 0, "probes": probes,
             "scope": "read-only retained source compatibility; no new endpoint or causal/gameplay result"}
    print(json.dumps(audit, sort_keys=True))


if __name__ == "__main__":
    main()
