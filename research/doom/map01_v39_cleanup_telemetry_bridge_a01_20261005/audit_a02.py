"""Stronger read-only audit of the retained A01 fake-display trace."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "SOURCE" / "A01"
OUT = HERE / "results" / "a02"


class AuditFailure(ValueError):
    pass


def need(ok: bool, reason: str) -> None:
    if not ok:
        raise AuditFailure(reason)


def nat(value: object) -> bool:
    return type(value) is int and value >= 0


def audit_raw(raw: dict, freeze: dict) -> dict:
    events = raw.get("bridge_emitted_events")
    cleanup = raw.get("owner_cleanup_record")
    need(raw.get("run_id") == freeze.get("run_id"), "run identity mismatch")
    need(type(events) is list and len(events) == 2, "expected two bridge-emitted rows")
    down, up = events
    need(type(down) is dict and type(up) is dict, "event rows must be objects")
    need(down.get("event") == "input_admission", "admission event missing")
    need(up.get("event") == "input_release_measurement", "later up call missing")
    for field in ("id", "step", "key", "intent_token", "owner_id"):
        need(down.get(field) == up.get(field), f"bridge event identity mismatch: {field}")
    need(type(down.get("id")) is str and bool(down["id"]), "program identity missing")
    need(type(down.get("step")) is int and down["step"] >= 0, "step must be exact nonnegative int")

    down_measure = down.get("physical_key_measurement")
    up_measure = up.get("physical_key_measurement")
    need(type(down_measure) is dict and type(up_measure) is dict, "bridge measurements missing")
    down_edge = down_measure.get("adapter_edge")
    need(down_measure.get("classification") == "CONFIRMED_PHYSICAL_DOWN"
         and down_measure.get("identity_status") == "MINTED", "down was not confirmed/minted")
    need(type(down_edge) is dict and down_edge.get("edge") == "down"
         and down_edge.get("status") == "CONFIRMED_PHYSICAL_DOWN", "confirmed down edge missing")
    actuation_id = down_measure.get("actuation_id")
    need(type(actuation_id) is str and bool(actuation_id)
         and down_edge.get("actuation_id") == actuation_id, "down actuation identity mismatch")
    down_bracket = down_measure.get("bracket")
    down_pre, down_post = down_measure.get("pre_sample"), down_measure.get("post_sample")
    need(type(down_bracket) is dict and type(down_pre) is dict and type(down_post) is dict,
         "down bracket and samples required")
    need(down_bracket.get("status") == "CONFIRMED_PHYSICAL_DOWN",
         "down bracket not confirmed")
    need(down_bracket.get("owner_id") == down.get("owner_id") == down_edge.get("owner_id")
         and down_bracket.get("intent_token") == down.get("intent_token") == down_edge.get("intent_token")
         and down_bracket.get("key") == down.get("key") == down_edge.get("key"),
         "down bracket identity mismatch")
    down_interval = down_bracket.get("physical_down_interval")
    need(type(down_interval) is list and len(down_interval) == 2
         and all(nat(x) for x in down_interval) and down_interval[0] <= down_interval[1],
         "down interval must be ordered exact integers")
    for name, sample in (("down pre", down_pre), ("down post", down_post)):
        need(sample.get("available") is True and sample.get("error") is None,
             f"{name} sample unavailable or errored")
        start, finish = sample.get("started_ns"), sample.get("finished_ns")
        need(nat(start) and nat(finish) and start <= finish,
             f"{name} sample timing invalid")
    need(down_pre.get("down") is False and down_post.get("down") is True,
         "down samples do not witness up-to-down state change")
    need(down_interval == [down_pre["finished_ns"], down_post["finished_ns"]],
         "down interval disagrees with sample endpoints")
    press, down_sync = down_measure.get("press_request_ns"), down_measure.get("sync_return_ns")
    need(nat(press) and nat(down_sync)
         and down_pre["finished_ns"] <= press <= down_sync <= down_post["finished_ns"],
         "press request/sync do not fit inside ordered down sample bracket")

    need(type(cleanup) is dict and cleanup.get("event") == "owner_release"
         and cleanup.get("reason") == "cancelled" and cleanup.get("verified") is True,
         "owner cancellation cleanup not verified")
    measurements = cleanup.get("per_key_release_measurements")
    need(type(measurements) is list and len(measurements) == 1,
         "expected exactly one per-key cleanup measurement")
    measured = measurements[0]
    need(measured.get("key") == down.get("key") == "F8", "cleanup key differs from admitted key")
    need(measured.get("classification") == "CONFIRMED_PHYSICAL_UP"
         and measured.get("identity_status") == "RETIRED"
         and measured.get("actuation_id") == actuation_id, "cleanup did not retire admitted hold")

    bracket = measured.get("bracket")
    pre, post = measured.get("pre_sample"), measured.get("post_sample")
    need(type(bracket) is dict and type(pre) is dict and type(post) is dict,
         "cleanup bracket and samples required")
    need(bracket.get("status") == "CONFIRMED_PHYSICAL_UP", "cleanup bracket not confirmed")
    need(bracket.get("owner_id") == down.get("owner_id") == down_edge.get("owner_id")
         and bracket.get("intent_token") == down.get("intent_token") == down_edge.get("intent_token")
         and bracket.get("key") == down.get("key") == down_edge.get("key"),
         "cleanup bracket identity mismatch")
    interval = bracket.get("physical_up_interval")
    need(type(interval) is list and len(interval) == 2 and all(nat(x) for x in interval)
         and interval[0] <= interval[1], "cleanup interval must be ordered exact integers")
    for name, sample in (("pre", pre), ("post", post)):
        need(sample.get("available") is True and sample.get("error") is None,
             f"{name} sample unavailable or errored")
        start, finish = sample.get("started_ns"), sample.get("finished_ns")
        need(nat(start) and nat(finish) and start <= finish,
             f"{name} sample timing invalid")
    need(pre.get("down") is True and post.get("down") is False,
         "samples do not witness down-to-up state change")
    need(interval == [pre["finished_ns"], post["finished_ns"]],
         "cleanup interval disagrees with sample endpoints")
    need(measured.get("release_attempted") is True, "owner release not attempted")
    request, sync = measured.get("release_request_ns"), measured.get("sync_return_ns")
    need(nat(request) and nat(sync)
         and pre["finished_ns"] <= request <= sync <= post["finished_ns"],
         "release request/sync do not fit inside ordered sample bracket")

    for row in (down, up):
        need(row.get("grants_input_authority", False) is False, "bridge row grants authority")
    for row in (down_measure, up_measure, down_edge, measured, bracket):
        need(row.get("grants_input_authority") is False, "measurement path grants authority")
    for row in (down_measure, up_measure, measured, bracket):
        need(row.get("application_consumption_observed") is False,
             "measurement path claims application effect")
    need(up_measure.get("classification") == "NOOP_ALREADY_UP"
         and up_measure.get("actuation_id") is None and up_measure.get("adapter_edge") is None,
         "later synchronous up must remain an unpaired noop")
    need("per_key_release_measurements" not in up, "bridge unexpectedly forwarded cleanup in A01")
    need(raw.get("fake_physical_keys_after_cleanup") == [], "fake display is not neutral")
    projected = raw.get("projected_receipts")
    need(type(projected) is list and len(projected) >= 1, "projector receipt missing")
    need(all(row.get("status") != "adapter_edge_brackets_paired" for row in projected)
         and all(row.get("up_edge_interval_ns") is None for row in projected),
         "projector paired evidence absent from bridge rows")
    return {
        "schema": "map01_v39_cleanup_telemetry_bridge_a02_audit_v1",
        "disposition": "PASS_AUDITED_GAP_REPRODUCED",
        "same_actuation_cleanup_up_confirmed": True,
        "down_interval_ns": down_interval,
        "cleanup_up_interval_ns": interval,
        "cleanup_verified_neutral": True,
        "sample_transition_verified": [True, False],
        "down_sample_transition_verified": [False, True],
        "release_timing_inside_sample_bracket": True,
        "bridge_forwarded_cleanup_measurement": False,
        "later_up_status": "NOOP_ALREADY_UP",
        "projector_receipts_unpaired": len(projected),
        "authority_granted": False,
        "application_effect_observed": False,
        "scope": "retained one-key fake-display bridge trace; no live OS input or game",
    }


def main() -> None:
    freeze_path = HERE / "FREEZE-A02.json"
    freeze_bytes = freeze_path.read_bytes()
    freeze = json.loads(freeze_bytes)
    for relative, digest in freeze["source_sha256"].items():
        data = (HERE / relative).read_bytes()
        need(hashlib.sha256(data).hexdigest() == digest, f"frozen source mismatch: {relative}")
    raw_bytes = (SOURCE / "RAW.json").read_bytes()
    need(hashlib.sha256(raw_bytes).hexdigest() == freeze["a01_raw_sha256"],
         "A01 raw hash mismatch")
    raw = json.loads(raw_bytes)
    a01_freeze_bytes = (SOURCE / "FREEZE.json").read_bytes()
    a01_freeze = json.loads(a01_freeze_bytes)
    need(hashlib.sha256(a01_freeze_bytes).hexdigest() == freeze["a01_freeze_sha256"],
         "A01 freeze hash mismatch")
    verdict = audit_raw(raw, a01_freeze)
    verdict.update({
        "a02_run_id": freeze["run_id"],
        "a01_raw_sha256": hashlib.sha256(raw_bytes).hexdigest(),
        "a01_freeze_sha256": hashlib.sha256(a01_freeze_bytes).hexdigest(),
        "a02_freeze_sha256": hashlib.sha256(freeze_bytes).hexdigest(),
        "candidate_rerun": False,
    })
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "AUDIT.json").write_text(json.dumps(verdict, indent=2, sort_keys=True) + "\n",
                                     encoding="utf-8", newline="\n")
    print(json.dumps(verdict, sort_keys=True))


if __name__ == "__main__":
    main()
