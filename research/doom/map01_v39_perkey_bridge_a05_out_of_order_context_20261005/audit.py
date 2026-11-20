from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


class AuditFailure(ValueError):
    pass


def need(condition, message):
    if not condition:
        raise AuditFailure(message)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    out = Path(parser.parse_args().out)
    freeze_path = HERE / "FREEZE.json"
    freeze = json.loads(freeze_path.read_text())
    scenario = json.loads((HERE / "scenario.json").read_text())
    for rel, expected in freeze["source_sha256"].items():
        need(digest(HERE / rel) == expected, f"frozen source mismatch: {rel}")
    raw_bytes = (out / "RAW.json").read_bytes()
    candidate_bytes = (out / "RESULT_CANDIDATE.json").read_bytes()
    raw = json.loads(raw_bytes)
    candidate = json.loads(candidate_bytes)
    need(digest(HERE / "scenario.json") == freeze["input_sha256"], "scenario hash mismatch")
    need(raw.get("run_id") == candidate.get("run_id") == freeze["run_id"], "run identity mismatch")
    need(raw.get("scenario") == scenario, "raw scenario mismatch")
    need(candidate.get("status") == "PENDING_INDEPENDENT_AUDIT", "candidate disposition mismatch")
    need(candidate.get("candidate_invocations") == 1 and type(candidate.get("candidate_invocations")) is int,
         "candidate invocation count mismatch")
    need(candidate.get("raw_sha256") == digest(out / "RAW.json"), "raw hash mismatch")
    need(candidate.get("freeze_sha256") == digest(freeze_path), "freeze hash mismatch")
    env = candidate.get("environment", {})
    need(env.get("container_image_id") == freeze["image"].split("@")[1], "container image identity mismatch")
    need(env.get("os_input") is False and env.get("gui") is False and env.get("game") is False
         and env.get("model_calls") == 0 and type(env.get("model_calls")) is int, "scope mismatch")

    expected_by_id = {item["actuation_id"]: item for item in scenario["admissions"]}
    baseline = raw.get("baseline", {})
    baseline_events = baseline.get("events", [])
    need(len(baseline_events) == 2, "baseline event count mismatch")
    baseline_misbound = 0
    for event in baseline_events:
        expected = expected_by_id[event["physical_key_measurement"]["actuation_id"]]
        if (event.get("id"), event.get("step")) != (expected["program_id"], expected["step"]):
            baseline_misbound += 1
    need(baseline_misbound == 1, "last-context baseline did not expose exactly one misbinding")

    a04 = raw.get("a04", {})
    events = a04.get("events", [])
    need(a04.get("cleanup_order") == scenario["cleanup_order"], "cleanup order mismatch")
    need([r.get("actuation_id") for r in a04.get("source_records", [])] == scenario["cleanup_order"],
         "source record order mismatch")
    need(len(events) == 2, "A04 release event count mismatch")
    seen = []
    for event in events:
        aid = event.get("physical_key_measurement", {}).get("actuation_id")
        expected = expected_by_id.get(aid)
        need(expected is not None, "unknown actuation emitted")
        seen.append(aid)
        need(event.get("event") == "input_release_measurement", "unexpected A04 event")
        need((event.get("id"), event.get("step"), event.get("owner_id"), event.get("intent_token"), event.get("key")) ==
             (expected["program_id"], expected["step"], expected["owner_id"], expected["intent_token"], expected["key"]),
             "A04 context or identity misbinding")
        measurement = event["physical_key_measurement"]
        need(measurement.get("classification") == "CONFIRMED_PHYSICAL_UP", "release not confirmed")
        edge = measurement.get("adapter_edge")
        need(edge and edge.get("actuation_id") == aid and edge.get("status") == "CONFIRMED_PHYSICAL_UP"
             and edge.get("grants_input_authority") is False, "release edge mismatch or authority escalation")
        need(event.get("grants_input_authority") is False and event.get("application_consumption_observed") is False,
             "event authority/effect boundary mismatch")
        source = event.get("owner_cleanup_record", {}).get("per_key_release_measurements", [])
        need(len(source) == 1 and source[0].get("actuation_id") == aid, "owner source record mismatch")
    need(seen == scenario["cleanup_order"], "A04 did not preserve observed cleanup order")
    need(a04.get("held") == [] and a04.get("active") == {} and a04.get("contexts") == {},
         "A04 did not retire all held/active/context state")

    result = {
        "schema": "map01-v39-perkey-bridge-a05-audit-v1",
        "run_id": freeze["run_id"],
        "disposition": "PASS_OUT_OF_ORDER_CONTEXT_SCOPED",
        "candidate_result_sha256": digest(out / "RESULT_CANDIDATE.json"),
        "raw_sha256": digest(out / "RAW.json"),
        "freeze_sha256": digest(freeze_path),
        "baseline_misbound_releases": baseline_misbound,
        "a04_correctly_bound_releases": len(events),
        "cleanup_order": seen,
        "authority_granted": False,
        "application_effect_observed": False,
        "scope": freeze["scope"],
    }
    (out / "AUDIT.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
