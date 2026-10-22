"""Strict consumer for retained InputOwner v12 per-key edge measurements."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


class EvidenceError(ValueError):
    pass


def _need(condition: bool, message: str) -> None:
    if not condition:
        raise EvidenceError(message)


def _int(value: object) -> bool:
    return type(value) is int and value >= 0


def _record_identity(row: dict) -> tuple:
    return (row.get("id"), row.get("step"), row.get("owner_id"),
            row.get("intent_token"), row.get("key"))


def _measurement(row: dict) -> tuple[dict, dict, list[int]]:
    measurement = row.get("physical_key_measurement")
    _need(type(measurement) is dict, "measurement must be an object")
    edge = measurement.get("adapter_edge")
    bracket = measurement.get("bracket")
    _need(type(edge) is dict and type(bracket) is dict,
          "edge and bracket objects are required")
    interval = edge.get("interval")
    _need(type(interval) is list and len(interval) == 2 and all(_int(x) for x in interval),
          "edge interval must contain two exact nonnegative integers")
    _need(interval == sorted(interval), "edge interval is reversed")
    _need(edge.get("owner_id") == row.get("owner_id"), "owner identity mismatch")
    _need(edge.get("intent_token") == row.get("intent_token"), "intent identity mismatch")
    _need(edge.get("key") == row.get("key"), "key identity mismatch")
    _need(measurement.get("grants_input_authority") is False,
          "measurement must not grant input authority")
    _need(measurement.get("application_consumption_observed") is False,
          "application consumption must remain unobserved")
    _need(row.get("grants_input_authority", False) is False,
          "event must not grant input authority")
    return measurement, bracket, interval


def reconstruct(events: list[dict]) -> dict:
    _need(type(events) is list and len(events) == 2,
          "exactly one retained down/up pair is required")
    down, up = events
    _need(type(down) is dict and type(up) is dict, "event rows must be objects")
    _need(down.get("event") == "input_admission", "down row event mismatch")
    _need(up.get("event") == "input_release_measurement", "up row event mismatch")
    _need(_record_identity(down) == _record_identity(up), "program/step/owner/intent/key mismatch")
    ident = _record_identity(down)
    _need(type(ident[0]) is str and ident[0], "program identifier is required")
    _need(type(ident[1]) is int and ident[1] >= 0, "step must be an exact nonnegative integer")
    _need(all(type(x) is str and x for x in ident[2:]), "owner, intent and key are required")

    dm, db, di = _measurement(down)
    um, ub, ui = _measurement(up)
    de, ue = dm["adapter_edge"], um["adapter_edge"]
    _need(dm.get("edge") == "down" and de.get("edge") == "down",
          "down measurement edge mismatch")
    _need(dm.get("classification") == "CONFIRMED_PHYSICAL_DOWN"
          and de.get("status") == "CONFIRMED_PHYSICAL_DOWN",
          "down edge is not confirmed")
    _need(dm.get("identity_status") == "MINTED", "down actuation was not minted")
    _need(um.get("edge") == "up" and ue.get("edge") == "up",
          "up measurement edge mismatch")
    _need(um.get("classification") == "CONFIRMED_PHYSICAL_UP"
          and ue.get("status") == "CONFIRMED_PHYSICAL_UP",
          "up edge is not confirmed")
    _need(um.get("identity_status") == "RETIRED", "up actuation was not retired")
    _need(dm.get("actuation_id") == de.get("actuation_id")
          and um.get("actuation_id") == ue.get("actuation_id")
          and de.get("actuation_id") == ue.get("actuation_id")
          and type(de.get("actuation_id")) is str and de.get("actuation_id"),
          "actuation identity mismatch")
    _need(db.get("status") == "CONFIRMED_PHYSICAL_DOWN"
          and db.get("physical_down_interval") == di,
          "down source bracket disagrees with edge interval")
    _need(ub.get("status") == "CONFIRMED_PHYSICAL_UP"
          and ub.get("physical_up_interval") == ui,
          "up source bracket disagrees with edge interval")
    _need(db.get("owner_id") == ub.get("owner_id") == ident[2]
          and db.get("intent_token") == ub.get("intent_token") == ident[3]
          and db.get("key") == ub.get("key") == ident[4],
          "source bracket identity mismatch")
    _need(type(de.get("grants_input_authority")) is bool
          and de["grants_input_authority"] is False
          and type(ue.get("grants_input_authority")) is bool
          and ue["grants_input_authority"] is False,
          "adapter edge must not grant authority")
    _need(type(dm.get("application_consumption_observed")) is bool
          and dm["application_consumption_observed"] is False
          and type(um.get("application_consumption_observed")) is bool
          and um["application_consumption_observed"] is False,
          "application effect must remain unobserved")
    _need(_int(down.get("admitted_ns")) and _int(down.get("input_ack_ns"))
          and down["admitted_ns"] <= down["input_ack_ns"],
          "down admission/ack chronology is invalid")
    dpre, dpost = dm.get("pre_sample"), dm.get("post_sample")
    upre, upost = um.get("pre_sample"), um.get("post_sample")
    _need(type(dpre) is dict and type(dpost) is dict and type(upre) is dict
          and type(upost) is dict, "sample witnesses must be objects")
    _need(_int(dm.get("press_request_ns")) and _int(dm.get("sync_return_ns"))
          and _int(dpre.get("finished_ns")) and _int(dpost.get("finished_ns")),
          "down timing witnesses are incomplete")
    _need(dpre["finished_ns"] <= dm["press_request_ns"]
          <= dm["sync_return_ns"] <= dpost["finished_ns"],
          "down operation timing is not ordered")
    _need(um.get("release_attempted") is True and _int(um.get("release_request_ns"))
          and _int(um.get("sync_return_ns"))
          and _int(upre.get("finished_ns")) and _int(upost.get("finished_ns")),
          "up release witnesses are incomplete")
    _need(upre["finished_ns"] <= um["release_request_ns"]
          <= um["sync_return_ns"] <= upost["finished_ns"],
          "up operation timing is not ordered")
    _need(di[1] <= ui[0], "down/up state brackets overlap or reverse")

    return {
        "schema": "map01_v39_perkey_sample_bracket_consumer_v1",
        "source_pair": {"program_id": ident[0], "step": ident[1],
                        "owner_id": ident[2], "intent_token": ident[3],
                        "key": ident[4], "actuation_id": de["actuation_id"]},
        "down_state_interval_ns": di,
        "up_state_interval_ns": ui,
        "hold_duration_lower_bound_ns": ui[0] - di[1],
        "hold_duration_upper_bound_ns": ui[1] - di[0],
        "authority_granted": False,
        "application_effect_observed": False,
        "scope": "fake-display sample-bracketed key-state duration; not exact physical/game occupancy"
    }


def load_events(path: Path, freeze_path: Path) -> tuple[bytes, list[dict]]:
    raw = path.read_bytes()
    freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
    expected = freeze.get("source_input", {}).get("sha256")
    _need(type(expected) is str and hashlib.sha256(raw).hexdigest() == expected,
          "input bytes do not match generated freeze")
    rows = [json.loads(line) for line in raw.decode("utf-8").splitlines() if line]
    return raw, rows
