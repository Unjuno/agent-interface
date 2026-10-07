"""Early typed DOOM observation bound to a later exact image artifact."""
import hashlib
from pathlib import Path
import time

from PIL import Image

from action_validity_admission_v1 import CONTRACT_FORMAT, SNAPSHOT_FORMAT


SCHEMA = "doom-typed-observation-v1"
SUPPORTED = {"health", "ammo"}


def frame_rgb_sha256(frame):
    if not isinstance(frame, Image.Image):
        raise ValueError("PIL frame required")
    rgb = frame.convert("RGB")
    return hashlib.sha256(rgb.tobytes()).hexdigest()


def _compact(result):
    required = {"format", "status", "signal_id", "value", "sequence",
                "capture_ns", "binding", "wad_sha256"}
    if (type(result) is not dict or not required <= set(result) or
            result["status"] not in ("observed", "unknown") or
            (result["status"] == "unknown" and result["value"] is not None)):
        raise ValueError("exact typed signal result required")
    compact = {key: result[key] for key in required}
    if result["status"] == "unknown":
        compact["reason"] = result.get("reason", "unspecified")
    return compact


def extract_typed_observation(frame, metadata, readers, clock=time.perf_counter_ns):
    expected = {"id", "step", "sequence", "capture_ns", "pointer_binding"}
    if (type(metadata) is not dict or set(metadata) != expected or
            type(metadata["sequence"]) is not int or metadata["sequence"] < 1 or
            type(metadata["capture_ns"]) is not int or metadata["capture_ns"] <= 0 or
            set(readers) != SUPPORTED):
        raise ValueError("exact capture metadata and health/ammo readers required")
    started_ns = clock()
    observation = dict(metadata)
    details = {name: readers[name].read_frame(observation, frame)
               for name in sorted(readers)}
    signals = {name: _compact(details[name]) for name in sorted(details)}
    ready_ns = clock()
    if not metadata["capture_ns"] <= started_ns <= ready_ns:
        raise ValueError("typed extraction clock must follow capture")
    rgb = frame.convert("RGB")
    return {
        "event": "typed_observation", "schema": SCHEMA,
        **metadata, "signals": signals,
        "frame_rgb_sha256": hashlib.sha256(rgb.tobytes()).hexdigest(),
        "frame_size": [rgb.width, rgb.height],
        "typed_extraction_started_ns": started_ns,
        "typed_ready_ns": ready_ns,
        "capture_to_typed_ready_ms": (ready_ns - metadata["capture_ns"]) / 1e6,
        "artifact_published": False,
        "grants_input_authority": False,
    }


def build_action_snapshot(event, contract):
    digest = event.get("frame_rgb_sha256") if type(event) is dict else None
    frame_size = event.get("frame_size") if type(event) is dict else None
    capture_ns = event.get("capture_ns") if type(event) is dict else None
    started_ns = event.get("typed_extraction_started_ns") if type(event) is dict else None
    ready_ns = event.get("typed_ready_ns") if type(event) is dict else None
    elapsed_ms = event.get("capture_to_typed_ready_ms") if type(event) is dict else None
    if (type(event) is not dict or event.get("event") != "typed_observation" or
            event.get("schema") != SCHEMA or
            type(contract) is not dict or contract.get("format") != CONTRACT_FORMAT or
            type(contract.get("source")) is not dict or
            type(contract["source"].get("signals")) is not dict or
            event.get("artifact_published") is not False or
            event.get("grants_input_authority") is not False or
            not isinstance(digest, str) or len(digest) != 64 or
            any(character not in "0123456789abcdef" for character in digest) or
            type(frame_size) is not list or len(frame_size) != 2 or
            any(type(value) is not int or value <= 0 for value in frame_size) or
            type(capture_ns) is not int or type(started_ns) is not int or
            type(ready_ns) is not int or not capture_ns <= started_ns <= ready_ns or
            type(elapsed_ms) not in (int, float) or
            abs(elapsed_ms - (ready_ns - capture_ns) / 1e6) > 1e-9):
        raise ValueError("exact early typed observation and action contract required")
    required = set(contract["source"]["signals"])
    if not required or not required <= SUPPORTED or set(event.get("signals", {})) != SUPPORTED:
        raise ValueError("complete typed health/ammo event required")
    signals = {}
    for name in sorted(required):
        row = event["signals"][name]
        if (type(row) is not dict or row.get("signal_id") != name or
                row.get("sequence") != event.get("sequence") or
                row.get("capture_ns") != event.get("capture_ns") or
                row.get("binding") != event.get("pointer_binding") or
                row.get("status") not in ("observed", "unknown") or
                (row.get("status") == "unknown" and row.get("value") is not None)):
            raise ValueError("typed signal must bind the exact early epoch")
        signals[name] = {"status": row["status"], "value": row["value"]}
    return {"format": SNAPSHOT_FORMAT, "sequence": event["sequence"],
            "capture_ns": event["capture_ns"],
            "binding": event["pointer_binding"], "signals": signals}


def reconcile_artifact(typed, observation, readers):
    checks = {
        "typed_schema": type(typed) is dict and typed.get("schema") == SCHEMA,
        "full_observation": type(observation) is dict and
                            observation.get("event") == "observation" and
                            observation.get("exact") is True,
        "same_epoch": all(typed.get(key) == observation.get(key)
                          for key in ("id", "step", "sequence", "capture_ns")),
        "same_binding": typed.get("pointer_binding") == observation.get("pointer_binding"),
    }
    try:
        with Image.open(Path(observation["image"])) as opened:
            artifact_hash = frame_rgb_sha256(opened)
    except (KeyError, OSError, ValueError):
        artifact_hash = None
    checks["rgb_hash"] = artifact_hash == typed.get("frame_rgb_sha256")
    results = {}
    for name in sorted(readers):
        try:
            results[name] = readers[name].read(observation)
            early = typed["signals"][name]
            checks[f"{name}_signal"] = (
                results[name].get("status") == early.get("status") and
                results[name].get("value") == early.get("value") and
                results[name].get("sequence") == early.get("sequence") and
                results[name].get("capture_ns") == early.get("capture_ns") and
                results[name].get("binding") == early.get("binding"))
        except (AttributeError, KeyError, TypeError, ValueError):
            checks[f"{name}_signal"] = False
    return {"schema": "doom-typed-artifact-reconciliation-v1",
            "matched": all(checks.values()), "checks": checks,
            "frame_rgb_sha256": typed.get("frame_rgb_sha256"),
            "artifact_rgb_sha256": artifact_hash,
            "artifact": observation.get("image") if type(observation) is dict else None}
