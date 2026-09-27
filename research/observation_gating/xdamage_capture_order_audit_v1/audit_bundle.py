#!/usr/bin/env python3
"""Independent read-only check of the published #3940 evidence capsule.

Uses only the capsule, standard-library decoders, and a separately written
X11 pixel/protocol oracle. It does not import the frozen runner or auditor.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import lzma
from pathlib import Path, PurePosixPath
import zlib

ARCHIVE_SHA256 = "a1f90fae8fe927b14cbc708cb09035cfa17ea500935bce330058e719b7dfe51a"
HEADER = b"P6\n96 64\n255\n"
EXPECTED_ALLOC = "xdamage-order-20260922-01"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def materialize(entry: dict) -> bytes:
    codec = entry.get("codec")
    if codec == "utf8":
        data = entry["text"].encode("utf-8")
    elif codec == "base64":
        data = base64.b64decode(entry["base64"], validate=True)
    else:
        raise ValueError(f"unsupported capsule codec: {codec!r}")
    if type(entry.get("nbytes")) is not int or len(data) != entry["nbytes"]:
        raise ValueError("capsule entry byte length mismatch")
    if sha(data) != entry.get("sha256"):
        raise ValueError("capsule entry SHA-256 mismatch")
    return data


def expected_image(shape: list[int], value: int | None) -> bytes:
    w, h = shape
    pixels = bytearray([32] * (96 * 64 * 3))
    if value is not None:
        for y in range(8, 8 + h):
            for x in range(8, 8 + w):
                offset = (y * 96 + x) * 3
                pixels[offset : offset + 3] = bytes((value,)) * 3
    return HEADER + pixels


def frozen_schedule(freeze: dict) -> list[dict]:
    schedule = freeze["schedule"]
    if len(schedule) != 120:
        raise ValueError("frozen formal denominator is not 120")
    return schedule


def protocol_signature(row: dict) -> list[tuple]:
    result = []
    for trace in row["trace"]:
        request = trace["request"]
        response = json.loads(trace["response_raw"])
        if response != trace["response"]:
            raise ValueError("parsed and raw native responses differ")
        if request is None:
            result.append((trace["role"], "ready"))
            continue
        words = request.split()
        op = words[0]
        if op == "draw":
            result.append((trace["role"], f"draw:{int(words[5])}"))
        elif op == "capture":
            result.append((trace["role"], f"capture:{Path(words[1]).stem}"))
        else:
            result.append((trace["role"], op))
    return result


def expected_protocol(spec: dict, gate_capture: bool) -> list[tuple]:
    p = spec["policy"]
    events = [
        ("writer", "ready"), ("observer", "ready"),
        ("writer", "capture:initial"), ("observer", "clear"),
        ("observer", "poll"), ("writer", "draw:64"), ("observer", "poll"),
    ]
    if spec["slot"] == "before":
        events.append(("writer", "draw:224"))
    cycle = [("observer", "capture:first"), ("observer", "clear")]
    if p == "clear_capture":
        cycle.reverse()
    events.append(cycle[0])
    if spec["slot"] in ("middle", "restore"):
        events.append(("writer", "draw:224"))
        if spec["slot"] == "restore":
            events.append(("writer", "draw:64"))
    events.append(cycle[1])
    if spec["slot"] == "after":
        events.append(("writer", "draw:224"))
    gate_index = len(events)
    events.append(("observer", "poll"))
    if gate_capture:
        next_cycle = [("observer", "capture:next"), ("observer", "clear")]
        if p == "clear_capture":
            next_cycle.reverse()
        events.extend(next_cycle)
    events.extend([("writer", "capture:truth"), ("observer", "clear"),
                   ("observer", "quit"), ("writer", "quit")])
    return events, gate_index


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("capsule", type=Path, nargs="?", default=Path(__file__).with_name("evidence.tar.xz"))
    args = parser.parse_args()
    errors: list[str] = []
    archive = args.capsule.read_bytes()
    if sha(archive) != ARCHIVE_SHA256:
        raise SystemExit("STOP: capsule SHA-256 mismatch")
    capsule = json.loads(lzma.decompress(archive))
    if capsule.get("schema") != "xdamage-lossless-evidence-v1":
        raise SystemExit("STOP: capsule schema mismatch")

    entries = capsule.get("files", {})
    decoded: dict[str, bytes] = {}
    for name, entry in entries.items():
        path = PurePosixPath(name)
        if path.is_absolute() or ".." in path.parts or "\\" in name:
            errors.append(f"unsafe capsule path: {name}")
            continue
        try:
            decoded[name] = materialize(entry)
        except (KeyError, ValueError, TypeError) as exc:
            errors.append(f"capsule entry {name}: {exc}")

    if len(decoded) != len(entries):
        errors.append("not all capsule entries decoded")
    freeze = json.loads(decoded["FREEZE.json"])
    if freeze.get("allocation") != EXPECTED_ALLOC or freeze.get("formal_invocations_at_freeze") != 0:
        errors.append("formal freeze identity mismatch")
    if len(freeze.get("schedule", [])) != 120:
        errors.append("frozen schedule denominator mismatch")

    meta_name = "formal/xdamage-order-20260922-01/metadata.json"
    rows_name = "formal/xdamage-order-20260922-01/rows.jsonl"
    meta = json.loads(decoded[meta_name])
    raw_rows = decoded[rows_name]
    rows = [json.loads(line) for line in raw_rows.splitlines()]
    specs = frozen_schedule(freeze)
    if meta.get("identities") != freeze.get("identities"):
        errors.append("formal source/environment identity differs from freeze")
    if len(rows) != len(specs):
        errors.append("raw row denominator mismatch")
    if meta.get("allocation") != EXPECTED_ALLOC or meta.get("formal_invocations") != 1:
        errors.append("formal allocation metadata mismatch")
    if meta.get("disposition") != "COMPLETED_UNSCORED" or meta.get("xvfb_exit") != 0:
        errors.append("formal process completion mismatch")
    if meta.get("identities") != meta.get("post_identities"):
        errors.append("source/environment changed during run")
    if meta.get("model_calls") != 0 or meta.get("input_injections") != 0:
        errors.append("excluded model/input activity present")

    counts = {
        p: {"rows": 0, "false_suppressions": 0, "middle_losses": 0,
            "after_correct": 0, "stable_correct": 0, "next_captures": 0,
            "redundant_captures": 0}
        for p in ("capture_clear", "clear_capture")
    }
    if len(rows) == len(specs):
        for row, spec in zip(rows, specs):
            rid = spec["id"]
            if {k: row.get(k) for k in spec} != spec:
                errors.append(f"{rid}: row/schedule identity mismatch")
                continue
            if row.get("error") or row.get("cleanup_errors"):
                errors.append(f"{rid}: recorded runtime/cleanup error")
            exits = row.get("exits", {})
            if set(exits) != {"writer", "observer"} or any(type(v) is not int or v != 0 for v in exits.values()):
                errors.append(f"{rid}: child exit mismatch")
            pids = row.get("pids", {})
            if set(pids) != {"writer", "observer"} or pids.get("writer") == pids.get("observer"):
                errors.append(f"{rid}: child identity mismatch")
            trace = row["trace"]
            clocks = [t.get("monotonic_ns") for t in trace]
            if any(type(v) is not int for v in clocks) or any(a >= b for a, b in zip(clocks, clocks[1:])):
                errors.append(f"{rid}: protocol clock order mismatch")

            gate = row["gate"]
            if type(gate.get("capture")) is not bool or type(gate.get("trace_index")) is not int:
                errors.append(f"{rid}: malformed gate")
                continue
            events, gate_index = expected_protocol(spec, gate["capture"])
            if protocol_signature(row) != events:
                errors.append(f"{rid}: protocol schedule mismatch")
            if gate["trace_index"] != gate_index or gate_index + 1 >= len(trace):
                errors.append(f"{rid}: gate boundary mismatch")
                continue
            gate_ns = gate.get("monotonic_ns")
            if type(gate_ns) is not int or not clocks[gate_index] < gate_ns < clocks[gate_index + 1]:
                errors.append(f"{rid}: gate timestamp outside its boundary")
            gate_response = trace[gate_index]["response"]
            if gate["capture"] != (gate_response.get("damage_count", 0) > 0):
                errors.append(f"{rid}: gate disagrees with native notification")
            for t in trace:
                response = t["response"]
                if response.get("event") == "poll":
                    if type(response.get("damage_count")) is not int or response["damage_count"] != len(response.get("events", [])):
                        errors.append(f"{rid}: notification count mismatch")

            frames = {}
            for label, packed in row["frames"].items():
                try:
                    image = zlib.decompress(base64.b64decode(packed["zlib_base64"], validate=True))
                    if type(packed.get("nbytes")) is not int or len(image) != packed["nbytes"] or sha(image) != packed.get("sha256"):
                        errors.append(f"{rid}: {label} frame byte/hash mismatch")
                    if not image.startswith(HEADER) or len(image) != len(HEADER) + 96 * 64 * 3:
                        errors.append(f"{rid}: {label} frame shape mismatch")
                    frames[label] = image
                except (KeyError, ValueError, zlib.error) as exc:
                    errors.append(f"{rid}: malformed {label} frame: {exc}")
            if set(frames) != ({"initial", "first", "truth", "next"} if gate["capture"] else {"initial", "first", "truth"}):
                errors.append(f"{rid}: capture/frame denominator mismatch")

            value = None
            for t in trace:
                req = t["request"]
                if req and req.startswith("draw "):
                    value = int(req.split()[5])
                elif req and req.startswith("capture "):
                    label = Path(req.split()[1]).stem
                    expected = expected_image(spec["shape"], value)
                    if frames.get(label) != expected:
                        errors.append(f"{rid}: independent pixel oracle mismatch for {label}")
            chosen_name = "next" if gate["capture"] else "first"
            if row.get("final_cache") != chosen_name:
                errors.append(f"{rid}: wrong selected cache frame")
            lost = frames.get(chosen_name) != frames.get("truth")
            counts[spec["policy"]]["rows"] += 1
            counts[spec["policy"]]["false_suppressions"] += int(lost)
            counts[spec["policy"]]["middle_losses"] += int(spec["slot"] == "middle" and lost)
            counts[spec["policy"]]["after_correct"] += int(spec["slot"] == "after" and gate["capture"] and not lost)
            counts[spec["policy"]]["stable_correct"] += int(spec["slot"] in ("none", "before", "restore") and not lost)
            counts[spec["policy"]]["next_captures"] += int(gate["capture"])
            counts[spec["policy"]]["redundant_captures"] += int(gate["capture"] and frames.get("first") == frames.get("truth"))

    expected_counts = {
        "capture_clear": {"rows": 60, "false_suppressions": 12, "middle_losses": 12,
                          "after_correct": 12, "stable_correct": 36, "next_captures": 12,
                          "redundant_captures": 0},
        "clear_capture": {"rows": 60, "false_suppressions": 0, "middle_losses": 0,
                          "after_correct": 12, "stable_correct": 36, "next_captures": 36,
                          "redundant_captures": 24},
    }
    if counts != expected_counts:
        errors.append("independent policy totals differ from frozen gates")
    archived_audit = json.loads(decoded["formal.audit.json"])
    result = {
        "audit": "PASS_INDEPENDENT_XDAMAGE_RAW_AGGREGATE_AUDIT" if not errors else "HOLD_INDEPENDENT_AUDIT",
        "capsule_sha256": sha(archive),
        "capsule_entries_verified": len(decoded),
        "capsule_file_count_field": capsule.get("file_count"),
        "formal_rows": len(rows),
        "raw_rows_sha256": sha(raw_rows),
        "archived_audit_report": {
            "decision": archived_audit.get("decision"),
            "integrity": archived_audit.get("integrity"),
            "errors": archived_audit.get("errors"),
            "corruption_controls_rejected": archived_audit.get("corruption_controls_rejected"),
        },
        "counts": counts,
        "errors": errors,
        "scope_limit": "Recomputes the packed aggregate raw rows; does not recreate omitted per-case filesystem receipts or rerun X11.",
    }
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0 if not errors else 2


if __name__ == "__main__":
    raise SystemExit(main())

