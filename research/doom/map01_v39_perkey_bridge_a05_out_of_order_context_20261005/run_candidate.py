from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import platform
import sys
import types
from pathlib import Path

HERE = Path(__file__).resolve().parent


def load_backend():
    base = types.ModuleType("doom_typed_release_backend_v1")
    base.Backend = type("Previous", (), {})
    base.suite = object()
    owner = types.ModuleType("input_owner_v13")
    owner.InputOwner = type("InputOwner", (), {})
    sys.modules[base.__name__] = base
    sys.modules[owner.__name__] = owner
    source = HERE / "SOURCE" / "bridge_a04.py"
    spec = importlib.util.spec_from_file_location("frozen_a04", source)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module.Backend


def cleanup_record(admission, timestamp):
    row = {
        "actuation_id": admission["actuation_id"],
        "owner_id": admission["owner_id"],
        "intent_token": admission["intent_token"],
        "key": admission["key"],
        "edge": "up",
        "classification": "CONFIRMED_PHYSICAL_UP",
        "bracket": {
            "owner_id": admission["owner_id"],
            "intent_token": admission["intent_token"],
            "key": admission["key"],
            "status": "CONFIRMED_PHYSICAL_UP",
            "physical_up_interval": [timestamp, timestamp + 2],
            "grants_input_authority": False,
        },
    }
    return {
        "event": "owner_release",
        "verified": True,
        "keys_down": [],
        "buttons_down": [],
        "per_key_release_measurements": [row],
    }


def invoke_a04(backend_type, scenario):
    backend = object.__new__(backend_type)
    backend.emit = lambda event: backend.events.append(event)
    backend.events = []
    backend.held = {item["key"] for item in scenario["admissions"]}
    backend._input_event_context = None
    backend._active_actuations = {
        (item["owner_id"], item["intent_token"], item["key"]): item["actuation_id"]
        for item in scenario["admissions"]
    }
    backend._actuation_context = {
        item["actuation_id"]: (item["program_id"], item["step"])
        for item in scenario["admissions"]
    }
    rows = []
    by_id = {item["actuation_id"]: item for item in scenario["admissions"]}
    for offset, actuation_id in enumerate(scenario["cleanup_order"]):
        record = cleanup_record(by_id[actuation_id], 100 + offset * 10)
        rows.append({"actuation_id": actuation_id, "record": record})
        backend._emit_owner_cleanup(record)
    return {
        "cleanup_order": list(scenario["cleanup_order"]),
        "source_records": rows,
        "events": backend.events,
        "held": sorted(backend.held),
        "active": backend._active_actuations,
        "contexts": backend._actuation_context,
    }


def invoke_last_context_baseline(scenario):
    # Deliberately weak comparator: every release uses the latest admitted context.
    last = scenario["admissions"][-1]
    by_id = {item["actuation_id"]: item for item in scenario["admissions"]}
    events = []
    for actuation_id in scenario["cleanup_order"]:
        item = by_id[actuation_id]
        events.append({
            "event": "input_release_measurement",
            "id": last["program_id"],
            "step": last["step"],
            "owner_id": item["owner_id"],
            "intent_token": item["intent_token"],
            "key": item["key"],
            "physical_key_measurement": {
                "actuation_id": actuation_id,
                "classification": "CONFIRMED_PHYSICAL_UP",
                "adapter_edge": {"status": "CONFIRMED_PHYSICAL_UP", "grants_input_authority": False},
            },
            "grants_input_authority": False,
        })
    return {"events": events, "held": [], "active": {}, "contexts": {}}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    out = Path(parser.parse_args().out)
    out.mkdir(parents=True, exist_ok=False)
    scenario = json.loads((HERE / "scenario.json").read_text())
    backend_type = load_backend()
    raw = {
        "run_id": scenario["run_id"],
        "scenario": scenario,
        "baseline": invoke_last_context_baseline(scenario),
        "a04": invoke_a04(backend_type, scenario),
    }
    raw_bytes = (json.dumps(raw, sort_keys=True, indent=2) + "\n").encode()
    (out / "RAW.json").write_bytes(raw_bytes)
    freeze_bytes = (HERE / "FREEZE.json").read_bytes()
    result = {
        "run_id": scenario["run_id"],
        "status": "PENDING_INDEPENDENT_AUDIT",
        "raw_sha256": hashlib.sha256(raw_bytes).hexdigest(),
        "freeze_sha256": hashlib.sha256(freeze_bytes).hexdigest(),
        "candidate_invocations": 1,
        "environment": {
            "container_image_id": os.environ.get("A05_IMAGE_ID"),
            "platform": platform.platform(),
            "python": platform.python_version(),
            "os_input": False,
            "gui": False,
            "game": False,
            "model_calls": 0,
        },
        "scope": "two-key in-memory reverse-order cleanup composition only",
    }
    (out / "RESULT_CANDIDATE.json").write_text(
        json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    print(json.dumps({"run_id": scenario["run_id"], "status": result["status"],
                      "raw_sha256": result["raw_sha256"],
                      "a04_bindings": [[e.get("id"), e.get("step"), e.get("key")]
                                       for e in raw["a04"]["events"]]}, sort_keys=True))


if __name__ == "__main__":
    main()
