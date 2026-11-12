"""Offline adapter from retained owner cancellation cleanup to strict V39 consumer."""
from __future__ import annotations

import copy


class ProjectionError(ValueError):
    pass


def need(ok: bool, message: str) -> None:
    if not ok:
        raise ProjectionError(message)


def nat(value: object) -> bool:
    return type(value) is int and value >= 0


def project_cleanup(raw: dict) -> list[dict]:
    rows = raw.get("bridge_emitted_events")
    cleanup = raw.get("owner_cleanup_record")
    need(type(rows) is list and len(rows) == 2, "two bridge events required")
    down, later_up = rows
    need(type(down) is dict and down.get("event") == "input_admission",
         "input admission required")
    need(type(later_up) is dict and later_up.get("event") == "input_release_measurement",
         "later bridge up receipt required")
    for field in ("id", "step", "owner_id", "intent_token", "key"):
        need(down.get(field) == later_up.get(field), f"bridge context mismatch: {field}")
    need(type(down.get("id")) is str and bool(down["id"]), "program context missing")
    need(type(down.get("step")) is int and down["step"] >= 0, "step must be exact nonnegative int")
    need(later_up.get("physical_key_measurement", {}).get("classification") == "NOOP_ALREADY_UP"
         and later_up["physical_key_measurement"].get("actuation_id") is None
         and later_up["physical_key_measurement"].get("adapter_edge") is None,
         "expected cancellation-racing later up to be an unpaired noop")
    dm = down.get("physical_key_measurement")
    need(type(dm) is dict and dm.get("classification") == "CONFIRMED_PHYSICAL_DOWN"
         and dm.get("identity_status") == "MINTED", "confirmed down admission required")
    aid = dm.get("actuation_id")
    de = dm.get("adapter_edge")
    need(type(aid) is str and bool(aid) and type(de) is dict
         and de.get("edge") == "down" and de.get("status") == "CONFIRMED_PHYSICAL_DOWN"
         and de.get("actuation_id") == aid, "down actuation identity invalid")

    need(type(cleanup) is dict and cleanup.get("event") == "owner_release"
         and cleanup.get("reason") == "cancelled" and cleanup.get("verified") is True
         and cleanup.get("keys_down") == [] and cleanup.get("buttons_down") == [],
         "verified cancellation cleanup required")
    per_key = cleanup.get("per_key_release_measurements")
    need(type(per_key) is list, "per-key cleanup list required")
    matched = [x for x in per_key if type(x) is dict and x.get("actuation_id") == aid]
    need(len(matched) == 1, "exactly one cleanup row must match down actuation")
    up = matched[0]
    need(up.get("edge") == "up" and up.get("classification") == "CONFIRMED_PHYSICAL_UP"
         and up.get("identity_status") == "RETIRED" and up.get("release_attempted") is True,
         "cleanup up must be confirmed and retire the down actuation")
    bracket = up.get("bracket")
    pre, post = up.get("pre_sample"), up.get("post_sample")
    need(type(bracket) is dict and type(pre) is dict and type(post) is dict,
         "cleanup bracket/samples missing")
    for field in ("owner_id", "intent_token", "key"):
        if field in up:
            need(up[field] == down.get(field), f"cleanup row identity mismatch: {field}")
        need(down.get(field) == bracket.get(field), f"cleanup bracket identity mismatch: {field}")
    interval = bracket.get("physical_up_interval")
    need(bracket.get("status") == "CONFIRMED_PHYSICAL_UP" and type(interval) is list
         and len(interval) == 2 and all(nat(v) for v in interval) and interval[0] <= interval[1],
         "cleanup interval invalid")
    need(pre.get("available") is True and pre.get("error") is None and pre.get("down") is True
         and post.get("available") is True and post.get("error") is None and post.get("down") is False,
         "cleanup samples do not confirm down-to-up state")
    for sample in (pre, post):
        need(nat(sample.get("started_ns")) and nat(sample.get("finished_ns"))
             and sample["started_ns"] <= sample["finished_ns"], "cleanup sample timing invalid")
    need(interval == [pre["finished_ns"], post["finished_ns"]],
         "cleanup interval differs from sample endpoints")
    request, sync = up.get("release_request_ns"), up.get("sync_return_ns")
    need(nat(request) and nat(sync)
         and pre["finished_ns"] <= request <= sync <= post["finished_ns"],
         "cleanup operation timing outside sample bracket")
    need(up.get("grants_input_authority") is False
         and up.get("application_consumption_observed") is False
         and bracket.get("grants_input_authority") is False
         and bracket.get("application_consumption_observed") is False,
         "cleanup measurement must remain non-authoritative and effect-unobserved")

    # Project only the owner cleanup measurement. Keep original context and the
    # entire source bracket; the synthetic adapter_edge is a typed view of that
    # bracket, not an independently observed edge time.
    projected_measurement = {
        "edge": "up", "classification": "CONFIRMED_PHYSICAL_UP",
        "bracket": copy.deepcopy(bracket), "actuation_id": aid,
        "identity_status": "RETIRED", "pre_sample": copy.deepcopy(pre),
        "post_sample": copy.deepcopy(post), "release_attempted": True,
        "release_request_ns": request, "sync_return_ns": sync,
        "adapter_edge": {
            "edge": "up", "status": "CONFIRMED_PHYSICAL_UP", "actuation_id": aid,
            "owner_id": down["owner_id"], "intent_token": down["intent_token"],
            "key": down["key"], "interval": list(interval),
            "grants_input_authority": False,
        },
        "grants_input_authority": False, "application_consumption_observed": False,
    }
    projected_up = {
        "event": "input_release_measurement", "id": down["id"], "step": down["step"],
        "owner_id": down["owner_id"], "intent_token": down["intent_token"],
        "key": down["key"], "grants_input_authority": False,
        "physical_key_measurement": projected_measurement,
    }
    return [copy.deepcopy(down), projected_up]
