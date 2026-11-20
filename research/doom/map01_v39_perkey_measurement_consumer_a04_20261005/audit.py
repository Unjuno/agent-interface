"""Independent raw-only audit for cancellation-cleanup consumer composition."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "SOURCE"


class AuditFailure(ValueError):
    pass


def need(ok: bool, message: str) -> None:
    if not ok:
        raise AuditFailure(message)


def nat(value: object) -> bool:
    return type(value) is int and value >= 0


def independently_project(raw: dict) -> list[dict]:
    """Reconstruct consumer rows from bridge event context and owner cleanup."""
    rows = raw.get("bridge_emitted_events")
    owner_release = raw.get("owner_cleanup_record")
    need(type(rows) is list and len(rows) == 2, "expected admission and later up rows")
    down, later = rows
    need(down.get("event") == "input_admission", "admission row missing")
    need(later.get("event") == "input_release_measurement", "later up row missing")
    for field in ("id", "step", "owner_id", "intent_token", "key"):
        need(down.get(field) == later.get(field), f"bridge context differs: {field}")
    need(type(down.get("id")) is str and bool(down["id"])
         and type(down.get("step")) is int and down["step"] >= 0,
         "admission program/step context invalid")
    later_measurement = later.get("physical_key_measurement")
    need(type(later_measurement) is dict
         and later_measurement.get("classification") == "NOOP_ALREADY_UP"
         and later_measurement.get("actuation_id") is None
         and later_measurement.get("adapter_edge") is None,
         "later raw up is not the expected unpaired cleanup race")

    down_measurement = down.get("physical_key_measurement")
    need(type(down_measurement) is dict
         and down_measurement.get("classification") == "CONFIRMED_PHYSICAL_DOWN"
         and down_measurement.get("identity_status") == "MINTED",
         "confirmed down measurement missing")
    actuation_id = down_measurement.get("actuation_id")
    down_edge = down_measurement.get("adapter_edge")
    need(type(actuation_id) is str and bool(actuation_id)
         and type(down_edge) is dict and down_edge.get("edge") == "down"
         and down_edge.get("status") == "CONFIRMED_PHYSICAL_DOWN"
         and down_edge.get("actuation_id") == actuation_id,
         "down actuation identity invalid")

    need(type(owner_release) is dict and owner_release.get("event") == "owner_release"
         and owner_release.get("reason") == "cancelled" and owner_release.get("verified") is True
         and owner_release.get("keys_down") == [] and owner_release.get("buttons_down") == [],
         "verified neutral cancellation cleanup missing")
    raw_per_key = owner_release.get("per_key_release_measurements")
    need(type(raw_per_key) is list, "per-key cleanup rows missing")
    matching = [r for r in raw_per_key
                if type(r) is dict and r.get("actuation_id") == actuation_id]
    need(len(matching) == 1, "cleanup must uniquely match the down actuation")
    cleanup = matching[0]
    need(cleanup.get("edge") == "up"
         and cleanup.get("classification") == "CONFIRMED_PHYSICAL_UP"
         and cleanup.get("identity_status") == "RETIRED"
         and cleanup.get("release_attempted") is True,
         "cleanup release did not confirm and retire the actuation")
    bracket = cleanup.get("bracket")
    pre, post = cleanup.get("pre_sample"), cleanup.get("post_sample")
    need(type(bracket) is dict and type(pre) is dict and type(post) is dict,
         "cleanup bracket/sample records missing")
    for field in ("owner_id", "intent_token", "key"):
        if field in cleanup:
            need(cleanup[field] == down.get(field), f"cleanup row identity mismatch: {field}")
        need(down.get(field) == bracket.get(field), f"cleanup bracket identity mismatch: {field}")
    interval = bracket.get("physical_up_interval")
    need(bracket.get("status") == "CONFIRMED_PHYSICAL_UP"
         and type(interval) is list and len(interval) == 2
         and all(nat(v) for v in interval) and interval[0] <= interval[1],
         "cleanup up interval invalid")
    need(pre.get("available") is True and pre.get("error") is None and pre.get("down") is True
         and post.get("available") is True and post.get("error") is None and post.get("down") is False,
         "cleanup sample state/availability invalid")
    for sample in (pre, post):
        need(nat(sample.get("started_ns")) and nat(sample.get("finished_ns"))
             and sample["started_ns"] <= sample["finished_ns"], "cleanup sample interval invalid")
    need(interval == [pre["finished_ns"], post["finished_ns"]],
         "cleanup interval differs from sample endpoints")
    request, sync = cleanup.get("release_request_ns"), cleanup.get("sync_return_ns")
    need(nat(request) and nat(sync)
         and pre["finished_ns"] <= request <= sync <= post["finished_ns"],
         "cleanup operation timing outside sample bracket")
    need(cleanup.get("grants_input_authority") is False
         and cleanup.get("application_consumption_observed") is False
         and bracket.get("grants_input_authority") is False
         and bracket.get("application_consumption_observed") is False,
         "cleanup measurement claims authority or application effect")

    consumer_measurement = {
        "edge": "up", "classification": "CONFIRMED_PHYSICAL_UP",
        "bracket": copy.deepcopy(bracket), "actuation_id": actuation_id,
        "identity_status": "RETIRED", "pre_sample": copy.deepcopy(pre),
        "post_sample": copy.deepcopy(post), "release_attempted": True,
        "release_request_ns": request, "sync_return_ns": sync,
        "adapter_edge": {
            "edge": "up", "status": "CONFIRMED_PHYSICAL_UP",
            "actuation_id": actuation_id, "owner_id": down["owner_id"],
            "intent_token": down["intent_token"], "key": down["key"],
            "interval": list(interval), "grants_input_authority": False,
        },
        "grants_input_authority": False, "application_consumption_observed": False,
    }
    up = {
        "event": "input_release_measurement", "id": down["id"], "step": down["step"],
        "owner_id": down["owner_id"], "intent_token": down["intent_token"],
        "key": down["key"], "grants_input_authority": False,
        "physical_key_measurement": consumer_measurement,
    }
    return [copy.deepcopy(down), up]


def load_a03_auditor(path: Path):
    spec = importlib.util.spec_from_file_location("independent_consumer_a03_auditor", path)
    if spec is None or spec.loader is None:
        raise AuditFailure("cannot load frozen A03 independent auditor")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.independently_reconstruct


def audit_result(raw: dict, result: dict, a03_oracle) -> dict:
    expected_events = independently_project(raw)
    need(result.get("projected_events") == expected_events,
         "candidate projected events differ from independent raw reconstruction")
    expected_consumer = a03_oracle(expected_events)
    need(result.get("candidate") == expected_consumer,
         "candidate result differs from independent strict-consumer reconstruction")
    need(result.get("status") == "PENDING_INDEPENDENT_AUDIT",
         "candidate status is not the expected pre-audit state")
    need(result.get("authority_granted") is False
         and result.get("application_effect_observed") is False,
         "candidate claims authority or application effect")
    need(result.get("candidate_invocations") == 1
         and result.get("new_os_input") is False
         and result.get("new_gui_or_game") is False
         and result.get("new_model_call") is False,
         "candidate scope receipt mismatch")
    return {
        "schema": "map01_v39_perkey_measurement_consumer_a04_audit_v1",
        "disposition": "PASS_CLEANUP_CONSUMER_COMPOSITION_SCOPED",
        "projected_event_count": len(expected_events),
        "program_id": expected_events[0]["id"], "step": expected_events[0]["step"],
        "key": expected_events[0]["key"],
        "actuation_id": expected_events[0]["physical_key_measurement"]["actuation_id"],
        "up_sample_interval_ns": expected_events[1]["physical_key_measurement"]["adapter_edge"]["interval"],
        "consumer_hold_duration_lower_bound_ns": expected_consumer["hold_duration_lower_bound_ns"],
        "consumer_hold_duration_upper_bound_ns": expected_consumer["hold_duration_upper_bound_ns"],
        "cleanup_bracket_preserved": True,
        "authority_granted": False, "application_effect_observed": False,
        "scope": "retained fake-display cleanup projected into strict consumer; not runtime integration",
    }


def main() -> None:
    freeze_bytes = (HERE / "FREEZE.json").read_bytes()
    freeze = json.loads(freeze_bytes)
    for relative, expected in freeze["source_sha256"].items():
        actual = hashlib.sha256((HERE / relative).read_bytes()).hexdigest()
        need(actual == expected, f"frozen source mismatch: {relative}")
    input_bytes = (SOURCE / "BRIDGE_RAW_A01.json").read_bytes()
    need(hashlib.sha256(input_bytes).hexdigest() == freeze["input_sha256"],
         "bridge raw input hash mismatch")
    result_bytes = (HERE / "RESULT.json").read_bytes()
    result = json.loads(result_bytes)
    raw = json.loads(input_bytes)
    need(result.get("input_sha256") == freeze["input_sha256"], "candidate input identity mismatch")
    need(result.get("freeze_sha256") == hashlib.sha256(freeze_bytes).hexdigest(),
         "candidate freeze identity mismatch")
    consumer_oracle = load_a03_auditor(SOURCE / "audit_a03.py")
    verdict = audit_result(raw, result, consumer_oracle)
    verdict.update({
        "run_id": freeze["run_id"],
        "input_sha256": hashlib.sha256(input_bytes).hexdigest(),
        "result_sha256": hashlib.sha256(result_bytes).hexdigest(),
        "freeze_sha256": hashlib.sha256(freeze_bytes).hexdigest(),
        "candidate_invocations": 1,
    })
    (HERE / "AUDIT.json").write_text(json.dumps(verdict, indent=2, sort_keys=True) + "\n",
                                      encoding="utf-8", newline="\n")
    print(json.dumps(verdict, sort_keys=True))


if __name__ == "__main__":
    main()
