"""Independent raw-only audit for MAP01-V39-CLEANUP-TELEMETRY-BRIDGE-A01."""
from __future__ import annotations

import copy
import hashlib
import json
import platform
import ast
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "SOURCE"
OUT = HERE / "results" / "a01"


def need(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def audit_raw(raw: dict, freeze: dict) -> dict:
    events = raw.get("bridge_emitted_events")
    cleanup = raw.get("owner_cleanup_record")
    need(raw.get("run_id") == freeze.get("run_id"), "run identity mismatch")
    need(type(events) is list and len(events) == 2, "expected two bridge-emitted rows")
    down, up = events
    need(down.get("event") == "input_admission", "admission event missing")
    need(up.get("event") == "input_release_measurement", "later up call missing")
    for field in ("id", "step", "key", "intent_token"):
        need(down.get(field) == up.get(field), f"program/key identity mismatch: {field}")
    down_measurement = down.get("physical_key_measurement", {})
    up_measurement = up.get("physical_key_measurement", {})
    down_edge = down_measurement.get("adapter_edge")
    need(down_measurement.get("classification") == "CONFIRMED_PHYSICAL_DOWN",
         "down edge was not independently confirmed")
    need(type(down_edge) is dict and down_edge.get("edge") == "down",
         "confirmed down adapter edge missing")
    actuation_id = down_edge.get("actuation_id")
    need(type(actuation_id) is str and actuation_id, "down actuation identity missing")
    need(cleanup.get("event") == "owner_release" and
         cleanup.get("reason") == "cancelled" and cleanup.get("verified") is True,
         "owner-thread cancellation cleanup not verified")
    measurements = cleanup.get("per_key_release_measurements")
    need(type(measurements) is list and len(measurements) == 1,
         "expected one per-key cleanup measurement")
    measured_up = measurements[0]
    need(measured_up.get("key") == down.get("key") == "F8",
         "cleanup key does not match admitted key")
    need(measured_up.get("classification") == "CONFIRMED_PHYSICAL_UP" and
         measured_up.get("identity_status") == "RETIRED" and
         measured_up.get("actuation_id") == actuation_id,
         "cleanup did not confirm the admitted actuation's up edge")
    bracket = measured_up.get("bracket")
    interval = bracket.get("physical_up_interval") if type(bracket) is dict else None
    pre = measured_up.get("pre_sample", {})
    post = measured_up.get("post_sample", {})
    need(type(interval) is list and len(interval) == 2 and
         all(type(x) is int for x in interval) and interval[0] <= interval[1],
         "cleanup up bracket is invalid")
    need(interval == [pre.get("finished_ns"), post.get("finished_ns")],
         "cleanup interval does not match retained samples")
    need(bracket.get("status") == "CONFIRMED_PHYSICAL_UP" and
         bracket.get("owner_id") == down_edge.get("owner_id") and
         bracket.get("intent_token") == down_edge.get("intent_token") and
         bracket.get("key") == down_edge.get("key"),
         "cleanup bracket identity mismatch")
    for item in (down_measurement, up_measurement, down_edge, measured_up, bracket):
        need(item.get("grants_input_authority") is False,
             "authority must remain false throughout")
    for item in (down_measurement, up_measurement, measured_up, bracket):
        need(item.get("application_consumption_observed") is False,
             "application effect must remain false throughout")
    for item in (down_edge,):
        if "application_consumption_observed" in item:
            need(item["application_consumption_observed"] is False,
                 "adapter edge must not assert application effect")
    need(up_measurement.get("classification") == "NOOP_ALREADY_UP" and
         up_measurement.get("actuation_id") is None and
         up_measurement.get("adapter_edge") is None,
         "later synchronous up call should lack the cleanup lineage")
    need("per_key_release_measurements" not in up,
         "cleanup measurement unexpectedly appeared in bridge telemetry")
    need(raw.get("fake_physical_keys_after_cleanup") == [],
         "fake display did not return to neutral")
    projected = raw.get("projected_receipts")
    need(type(projected) is list and len(projected) >= 1,
         "projector emitted no receipt")
    need(all(row.get("status") != "adapter_edge_brackets_paired" for row in projected),
         "projector paired a release that bridge telemetry does not carry")
    need(all(row.get("up_edge_interval_ns") is None for row in projected),
         "projector exposed an up interval absent from bridge telemetry")
    return {
        "status": "PASS_GAP_REPRODUCED",
        "same_actuation_cleanup_up_confirmed": True,
        "cleanup_interval_ns": interval,
        "cleanup_verified_neutral": True,
        "bridge_forwarded_cleanup_measurement": False,
        "later_up_status": "NOOP_ALREADY_UP",
        "projector_receipt_count": len(projected),
        "projector_has_paired_receipt": False,
        "projector_up_intervals": [row.get("up_edge_interval_ns") for row in projected],
        "authority_granted": False,
        "application_effect_observed": False,
        "scope": freeze["scope"],
    }


def projector_from_source(path: Path):
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    function = next(n for n in tree.body
                    if isinstance(n, ast.FunctionDef) and n.name == "input_edge_receipts")
    namespace = {"hashlib": hashlib}
    exec(compile(ast.Module(body=[function], type_ignores=[]), str(path), "exec"), namespace)
    return namespace["input_edge_receipts"]


def normalized_cleanup_control(raw: dict, projector) -> dict:
    """Post-hoc schema probe; this row was not emitted by the candidate bridge."""
    down = raw["bridge_emitted_events"][0]
    measured_up = copy.deepcopy(
        raw["owner_cleanup_record"]["per_key_release_measurements"][0])
    bracket = measured_up["bracket"]
    normalized = {
        "event": "input_release_measurement",
        "id": down["id"],
        "step": down["step"],
        "key": measured_up["key"],
        "owner_id": bracket["owner_id"],
        "intent_token": bracket["intent_token"],
        "grants_input_authority": False,
        "physical_key_measurement": {
            **measured_up,
            "adapter_edge": {
                "edge": "up",
                "status": "CONFIRMED_PHYSICAL_UP",
                "actuation_id": measured_up["actuation_id"],
                "owner_id": bracket["owner_id"],
                "intent_token": bracket["intent_token"],
                "key": measured_up["key"],
                "interval": bracket["physical_up_interval"],
                "grants_input_authority": False,
            },
        },
    }
    without_adapter_edge = copy.deepcopy(normalized)
    without_adapter_edge["physical_key_measurement"].pop("adapter_edge")
    bare = projector([down, without_adapter_edge])
    paired = projector([down, normalized])
    need(all(row.get("status") != "adapter_edge_brackets_paired" for row in bare),
         "owner cleanup unexpectedly pairs without an adapter-edge projection")
    need(len(paired) == 1 and paired[0].get("status") == "adapter_edge_brackets_paired",
         "normalized cleanup schema did not pair with its admitted down")
    need(paired[0].get("up_edge_interval_ns") ==
         measured_up["bracket"]["physical_up_interval"],
         "normalized projector interval differs from owner cleanup samples")
    return {
        "status_without_adapter_edge": [x.get("status") for x in bare],
        "status_with_synthesized_adapter_edge": paired[0]["status"],
        "up_edge_interval_ns": paired[0]["up_edge_interval_ns"],
        "candidate_bridge_emitted_this_control": False,
        "scope": "post-hoc schema-only projection control; not runtime integration evidence",
    }


def main() -> None:
    freeze_path = HERE / "FREEZE.json"
    freeze_bytes = freeze_path.read_bytes()
    freeze = json.loads(freeze_bytes)
    need(platform.python_version() == freeze["python_version"], "Python version mismatch")
    for name, digest in freeze["sources"].items():
        need(hashlib.sha256((SOURCE / name).read_bytes()).hexdigest() == digest,
             f"frozen source hash mismatch: {name}")
    raw_path = OUT / "RAW.json"
    raw_bytes = raw_path.read_bytes()
    raw = json.loads(raw_bytes)
    verdict = audit_raw(raw, freeze)
    projector = projector_from_source(SOURCE / "controller_v39_projector.py")
    verdict["posthoc_normalization_control"] = normalized_cleanup_control(raw, projector)

    mutations = []
    controls = []
    cases = [
        ("cleanup_actuation_alias", lambda x: x["owner_cleanup_record"]["per_key_release_measurements"][0].__setitem__("actuation_id", "other")),
        ("cleanup_authority_true", lambda x: x["owner_cleanup_record"]["per_key_release_measurements"][0].__setitem__("grants_input_authority", True)),
        ("invent_projector_up_interval", lambda x: x["projected_receipts"][0].__setitem__("up_edge_interval_ns", [1, 2])),
    ]
    for name, mutate in cases:
        damaged = copy.deepcopy(raw)
        mutate(damaged)
        try:
            audit_raw(damaged, freeze)
        except (KeyError, TypeError, ValueError):
            controls.append({"case": name, "status": "REJECTED"})
        else:
            controls.append({"case": name, "status": "ACCEPTED_UNEXPECTEDLY"})
    verdict["mutation_controls"] = controls
    verdict["mutation_controls_passed"] = all(x["status"] == "REJECTED" for x in controls)
    verdict["raw_sha256"] = hashlib.sha256(raw_bytes).hexdigest()
    verdict["freeze_sha256"] = hashlib.sha256(freeze_bytes).hexdigest()
    need(verdict["mutation_controls_passed"], "auditor mutation control accepted corruption")
    (OUT / "AUDIT.json").write_text(
        json.dumps(verdict, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(verdict, sort_keys=True))


if __name__ == "__main__":
    main()
