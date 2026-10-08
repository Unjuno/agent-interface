#!/usr/bin/env python3
"""Read-only #4193 retained-source schema compatibility analysis (stdlib only)."""
import hashlib
import json
import lzma
import sys
from pathlib import Path

EXPECTED_SHA256 = "0d55f782f0e129738b422e52d8066f7fb69a02ebcf2c1691ee711e74a369a740"
EXPECTED_KEYS = {
    "p1-attack", "p1-noinput", "p2-attack", "p2-noinput",
    "p3-attack", "p3-noinput",
}


def read_source(path):
    compressed = Path(path).read_bytes()
    digest = hashlib.sha256(compressed).hexdigest()
    if digest != EXPECTED_SHA256:
        raise ValueError(f"source SHA-256 mismatch: {digest}")
    data = json.loads(lzma.decompress(compressed))
    if set(data) != EXPECTED_KEYS:
        raise ValueError("unexpected session keys")
    return data


def parse_lines(values):
    return [json.loads(line) for line in values]


def contains_key(value, target):
    if isinstance(value, dict):
        return target in value or any(contains_key(item, target) for item in value.values())
    if isinstance(value, list):
        return any(contains_key(item, target) for item in value)
    return False


def inspect_session(name, session):
    events = parse_lines(session["events_exact_jsonl"])
    samples = parse_lines(session["scorer_samples_exact_jsonl"])
    if not samples:
        raise ValueError(f"{name}: missing scorer samples")
    payloads = [item["payload"] for item in samples]
    if any(p.get("schema") != "independent-progress-sample-v2" for p in payloads):
        raise ValueError(f"{name}: unexpected scorer schema")
    times = [p["sample_ns"] for p in payloads]
    if any(b <= a for a, b in zip(times, times[1:])):
        raise ValueError(f"{name}: scorer timestamps not strictly increasing")

    positive = []
    baseline = payloads[0]["kill_count"]
    previous_exit = bool(payloads[0]["map_exit"])
    for index, payload in enumerate(payloads):
        if payload["kill_count"] > baseline:
            positive.append({
                "locator": [name, index, payload["sample_ns"], "KILL_COUNT_INCREASE"],
                "value": payload["kill_count"],
            })
        current_exit = bool(payload["map_exit"])
        if current_exit and not previous_exit:
            positive.append({
                "locator": [name, index, payload["sample_ns"], "MAP_EXIT"],
                "value": True,
            })
        previous_exit = current_exit

    result = {
        "session_key": name,
        "sample_count": len(samples),
        "sample_ns_strictly_increasing_within_session": True,
        "all_kill_count_zero": all(p["kill_count"] == 0 for p in payloads),
        "any_map_exit": any(bool(p["map_exit"]) for p in payloads),
        "positive_endpoint_count": len(positive),
        "positive_endpoints": positive,
        "native_source_event_id_present": contains_key(session, "source_event_id"),
        "native_scorer_event_id_present": contains_key(session, "scorer_event_id"),
    }

    if name.endswith("-attack"):
        admission = [e for e in events if e.get("event") == "input_admission"]
        release = [e for e in events if e.get("event") == "input_release_transition"]
        if len(admission) != 1 or len(release) != 1:
            raise ValueError(f"{name}: expected exactly one admission and release")
        down_m = admission[0]["physical_key_measurement"]
        up_m = release[0]["physical_key_measurement"]
        down, up = down_m["bracket"], up_m["bracket"]
        down_edge, up_edge = down_m["adapter_edge"], up_m["adapter_edge"]
        checks = {
            "down_confirmed": down.get("status") == "CONFIRMED_PHYSICAL_DOWN",
            "up_confirmed": up.get("status") == "CONFIRMED_PHYSICAL_UP",
            "down_adapter_edge_confirmed": down_edge.get("edge") == "down" and down_edge.get("status") == "CONFIRMED_PHYSICAL_DOWN",
            "up_adapter_edge_confirmed": up_edge.get("edge") == "up" and up_edge.get("status") == "CONFIRMED_PHYSICAL_UP",
            "press_id_present": bool(down.get("press_id")),
            "release_id_present": bool(up.get("release_id")),
            "actuation_id_present": bool(down_edge.get("actuation_id")),
            "actuation_id_equal": down_edge.get("actuation_id") == up_edge.get("actuation_id"),
            "owner_id_present": bool(down.get("owner_id")),
            "intent_token_present": bool(down.get("intent_token")),
            "key_present": bool(down.get("key")),
            "owner_id_equal": down.get("owner_id") == up.get("owner_id") == down_edge.get("owner_id") == up_edge.get("owner_id"),
            "intent_token_equal": down.get("intent_token") == up.get("intent_token") == down_edge.get("intent_token") == up_edge.get("intent_token"),
            "key_equal": down.get("key") == up.get("key") == down_edge.get("key") == up_edge.get("key"),
            "down_edge_matches_bracket": down_edge.get("interval") == down.get("physical_down_interval"),
            "up_edge_matches_bracket": up_edge.get("interval") == up.get("physical_up_interval"),
        }
        result["physical_receipt_checks"] = checks
        result["physical_receipt_join_supported"] = all(checks.values())
        result["native_receipt_ids"] = {
            "press_id": down.get("press_id"),
            "release_id": up.get("release_id"),
            "actuation_id": down_edge.get("actuation_id"),
            "owner_id": down.get("owner_id"),
            "intent_token": down.get("intent_token"),
            "key": down.get("key"),
        }
    else:
        if any(e.get("event") in {"input_admission", "input_release_transition"} for e in events):
            raise ValueError(f"{name}: no-input session contains input edge")
        result["physical_receipt_join_supported"] = None
    return result


def main():
    if len(sys.argv) != 3:
        raise SystemExit("usage: runner.py RAW_USED.json.xz RESULT.json")
    data = read_source(sys.argv[1])
    sessions = [inspect_session(name, data[name]) for name in sorted(data)]
    attacks = [s for s in sessions if s["session_key"].endswith("-attack")]
    noinputs = [s for s in sessions if s["session_key"].endswith("-noinput")]
    joins_pass = all(s["physical_receipt_join_supported"] for s in attacks)
    attack_positive = sum(s["positive_endpoint_count"] > 0 for s in attacks)
    noinput_positive = sum(s["positive_endpoint_count"] > 0 for s in noinputs)
    result = {
        "study": "4193-retained-source-schema-compatibility-v3",
        "source_sha256": EXPECTED_SHA256,
        "source_bytes": Path(sys.argv[1]).stat().st_size,
        "session_count": len(sessions),
        "attack_sessions": len(attacks),
        "attack_physical_joins_supported": sum(s["physical_receipt_join_supported"] for s in attacks),
        "attack_sessions_with_positive_scorer_endpoint": attack_positive,
        "noinput_sessions_with_positive_scorer_endpoint": noinput_positive,
        "attack_positive_endpoint_total": sum(s["positive_endpoint_count"] for s in attacks),
        "noinput_positive_endpoint_total": sum(s["positive_endpoint_count"] for s in noinputs),
        "scorer_sample_total": sum(s["sample_count"] for s in sessions),
        "native_source_event_id_present_anywhere": any(s["native_source_event_id_present"] for s in sessions),
        "native_scorer_event_id_present_anywhere": any(s["native_scorer_event_id_present"] for s in sessions),
        "disposition": "HOLD_NO_POSITIVE_SCORER_EVENT" if joins_pass and attack_positive == 0 else "FAIL_OR_REVIEW",
        "sessions": sessions,
    }
    Path(sys.argv[2]).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k != "sessions"}, sort_keys=True))


if __name__ == "__main__":
    main()
