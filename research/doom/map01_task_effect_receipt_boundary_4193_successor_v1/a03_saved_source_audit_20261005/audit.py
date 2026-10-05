#!/usr/bin/env python3
"""Independent read-only audit of the retained #4193 JSON-in-JSONL source."""
import argparse
import copy
import hashlib
import json
import lzma
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
SOURCE = ROOT / "research/doom/map01_v12_attack_task_effect_live_v1/RAW_USED.json.xz"
EXPECTED_SHA256 = "0d55f782f0e129738b422e52d8066f7fb69a02ebcf2c1691ee711e74a369a740"
EXPECTED_SESSIONS = {f"p{i}-{arm}" for i in range(1, 4) for arm in ("attack", "noinput")}
EXPECTED_SAMPLE_COUNTS = {
    "p1-attack": 32, "p1-noinput": 32,
    "p2-attack": 34, "p2-noinput": 32,
    "p3-attack": 32, "p3-noinput": 32,
}


class AuditError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise AuditError(message)


def contains_key(value, wanted):
    if type(value) is dict:
        return wanted in value or any(contains_key(item, wanted) for item in value.values())
    if type(value) is list:
        return any(contains_key(item, wanted) for item in value)
    return False


def parse_json_string_rows(rows, label):
    require(type(rows) is list, f"{label}: expected array of JSON strings")
    parsed = []
    for index, row in enumerate(rows):
        require(type(row) is str, f"{label}[{index}]: expected exact string")
        try:
            item = json.loads(row)
        except (ValueError, TypeError) as exc:
            raise AuditError(f"{label}[{index}]: malformed JSON string") from exc
        require(type(item) is dict, f"{label}[{index}]: expected JSON object")
        parsed.append(item)
    return parsed


def check_physical_join(admission, release, session_name):
    am = admission.get("physical_key_measurement")
    rm = release.get("physical_key_measurement")
    require(type(am) is dict and type(rm) is dict, f"{session_name}: missing physical measurement")
    ab, rb = am.get("bracket"), rm.get("bracket")
    ae, re = am.get("adapter_edge"), rm.get("adapter_edge")
    require(all(type(x) is dict for x in (ab, rb, ae, re)), f"{session_name}: missing bracket/adapter edge")
    require((am.get("edge"), rm.get("edge")) == ("down", "up"), f"{session_name}: wrong measurement edges")
    require((ab.get("status"), ae.get("status")) ==
            ("CONFIRMED_PHYSICAL_DOWN", "CONFIRMED_PHYSICAL_DOWN"),
            f"{session_name}: down edge is not confirmed")
    require((rb.get("status"), re.get("status")) ==
            ("CONFIRMED_PHYSICAL_UP", "CONFIRMED_PHYSICAL_UP"),
            f"{session_name}: up edge is not confirmed")
    # actuation_id is carried by the measurement and adapter edge; bracket
    # identity carries owner/intent/key but intentionally has no actuation_id.
    identity = ("owner_id", "intent_token", "key")
    for key in identity:
        values = (ae.get(key), re.get(key), ab.get(key), rb.get(key))
        require(type(values[0]) is str and bool(values[0]) and all(v == values[0] for v in values),
                f"{session_name}: DOWN/UP {key} mismatch")
    require(am.get("actuation_id") == rm.get("actuation_id") == ae["actuation_id"] == re["actuation_id"],
            f"{session_name}: measurement actuation mismatch")
    require(admission.get("key") == release.get("key") == ae["key"],
            f"{session_name}: event key mismatch")
    require(admission.get("intent_token") == release.get("intent_token") == ae["intent_token"],
            f"{session_name}: event intent mismatch")
    require(release.get("owner_id") == ae["owner_id"], f"{session_name}: release owner mismatch")
    require(type(ab.get("press_id")) is str and bool(ab["press_id"]), f"{session_name}: missing press ID")
    require(type(rb.get("release_id")) is str and bool(rb["release_id"]), f"{session_name}: missing release ID")
    for bracket, interval_key in ((ab, "physical_down_interval"), (rb, "physical_up_interval")):
        interval = bracket.get(interval_key)
        require(type(interval) is list and len(interval) == 2 and
                all(type(n) is int for n in interval) and interval[0] < interval[1],
                f"{session_name}: invalid {interval_key}")
    for row in (ab, rb, ae, re):
        require(row.get("grants_input_authority") is False,
                f"{session_name}: physical evidence grants authority")
    require(ab.get("application_consumption_observed") is False and
            rb.get("application_consumption_observed") is False,
            f"{session_name}: application consumption was asserted")


def audit_document(document):
    require(type(document) is dict and set(document) == EXPECTED_SESSIONS,
            "session inventory differs from freeze")
    summary = {
        "source_sha256": EXPECTED_SHA256,
        "sessions": len(document),
        "sample_counts": {},
        "sample_total": 0,
        "physical_down_up_joins": 0,
        "attack_positive_endpoint_transitions": 0,
        "noinput_positive_endpoint_transitions": 0,
        "native_source_event_id_present": False,
        "native_scorer_event_id_present": False,
    }
    for name in sorted(EXPECTED_SESSIONS):
        session = document[name]
        require(type(session) is dict, f"{name}: session is not an object")
        events = parse_json_string_rows(session.get("events_exact_jsonl"), f"{name}.events_exact_jsonl")
        samples = parse_json_string_rows(session.get("scorer_samples_exact_jsonl"),
                                         f"{name}.scorer_samples_exact_jsonl")
        require(len(samples) == EXPECTED_SAMPLE_COUNTS[name], f"{name}: sample count differs from freeze")
        summary["sample_counts"][name] = len(samples)
        summary["sample_total"] += len(samples)
        require(not any(contains_key(row, "source_event_id") for row in events + samples),
                f"{name}: producer source_event_id unexpectedly present")
        require(not any(contains_key(row, "scorer_event_id") for row in events + samples),
                f"{name}: producer scorer_event_id unexpectedly present")
        times, kills, exits = [], [], []
        for index, row in enumerate(samples):
            payload = row.get("payload")
            require(type(payload) is dict and payload.get("schema") == "independent-progress-sample-v2",
                    f"{name}[{index}]: wrong scorer sample schema")
            sample_ns, kill_count, map_exit = (payload.get("sample_ns"),
                                               payload.get("kill_count"),
                                               payload.get("map_exit"))
            require(type(sample_ns) is int and type(kill_count) is int and type(map_exit) is bool,
                    f"{name}[{index}]: scorer endpoint fields have wrong exact types")
            require(kill_count == 0 and map_exit is False,
                    f"{name}[{index}]: unexpected retained positive endpoint state")
            times.append(sample_ns)
            kills.append(kill_count)
            exits.append(map_exit)
        require(all(left < right for left, right in zip(times, times[1:])),
                f"{name}: scorer sample_ns is not strictly increasing within session")
        if name.endswith("-attack"):
            admissions = [e for e in events if e.get("event") == "input_admission"]
            releases = [e for e in events if e.get("event") == "input_release_transition"]
            require(len(admissions) == len(releases) == 1, f"{name}: expected one admission/release pair")
            check_physical_join(admissions[0], releases[0], name)
            summary["physical_down_up_joins"] += 1
            baseline = kills[0]
            summary["attack_positive_endpoint_transitions"] += sum(k > baseline for k in kills)
            summary["attack_positive_endpoint_transitions"] += sum(
                not before and after for before, after in zip(exits, exits[1:]))
        else:
            require(not any(e.get("event") in ("input_admission", "input_release_transition")
                            for e in events), f"{name}: no-input session contains an input event")
            baseline = kills[0]
            summary["noinput_positive_endpoint_transitions"] += sum(k > baseline for k in kills)
            summary["noinput_positive_endpoint_transitions"] += sum(
                not before and after for before, after in zip(exits, exits[1:]))
    require(summary["sample_total"] == 194, "total scorer sample count differs from freeze")
    require(summary["physical_down_up_joins"] == 3, "attack physical joins differ from freeze")
    require(summary["attack_positive_endpoint_transitions"] == 0 and
            summary["noinput_positive_endpoint_transitions"] == 0,
            "positive endpoint transition found")
    summary["disposition"] = "HOLD_NO_POSITIVE_SCORER_EVENT"
    summary["status"] = "PASS_READ_ONLY_SAVED_SOURCE"
    summary["scope"] = "hash-pinned retained data only; no positive task effect or live efficacy claim"
    return summary


def load_and_audit(path=SOURCE):
    blob = Path(path).read_bytes()
    digest = hashlib.sha256(blob).hexdigest()
    require(digest == EXPECTED_SHA256, "retained source SHA-256 mismatch")
    try:
        document = json.loads(lzma.decompress(blob))
    except (lzma.LZMAError, json.JSONDecodeError) as exc:
        raise AuditError("retained source failed decompression or JSON parsing") from exc
    return audit_document(document)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path(__file__).parent / "results/AUDIT.json")
    args = parser.parse_args()
    result = load_and_audit()
    encoded = json.dumps(result, indent=2, sort_keys=True) + "\n"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(encoded, encoding="utf-8")
    print(encoded, end="")


if __name__ == "__main__":
    main()
