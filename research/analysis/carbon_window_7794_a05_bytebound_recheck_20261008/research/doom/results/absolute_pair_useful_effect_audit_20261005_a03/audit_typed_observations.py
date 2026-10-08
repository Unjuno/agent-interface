import argparse
import hashlib
import json
from pathlib import Path
import subprocess


CELLS = ("00-coast", "01-pulse", "02-pulse", "03-coast", "04-coast", "05-pulse")
SIGNALS = ("health", "ammo")


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def audit(root, freeze, auditor_path):
    errors = []
    cells = []
    main_blob_checks = 0
    repository = root.resolve().parents[2]
    if sha256(auditor_path) != freeze.get("auditor_sha256"):
        errors.append("auditor_hash_mismatch")
    if tuple(freeze.get("cells", ())) != CELLS:
        errors.append("cell_inventory_mismatch")

    for name in CELLS:
        base = root / name
        event_path = base / "runtime" / "events.jsonl"
        result_path = base / "RESULT.json"
        expected = freeze.get("inputs", {}).get(name, {})
        if not event_path.is_file() or sha256(event_path) != expected.get("events_sha256"):
            errors.append(name + ":events_hash_mismatch")
            continue
        if not result_path.is_file() or sha256(result_path) != expected.get("result_sha256"):
            errors.append(name + ":result_hash_mismatch")
            continue
        for path, key in ((event_path, "events_sha256"), (result_path, "result_sha256")):
            relative = path.resolve().relative_to(repository).as_posix()
            try:
                committed = subprocess.run(
                    ["git", "show", freeze["main_commit"] + ":" + relative],
                    cwd=repository, check=True, capture_output=True,
                ).stdout
            except (KeyError, OSError, subprocess.CalledProcessError):
                errors.append(name + ":main_blob_unavailable:" + key)
                continue
            if hashlib.sha256(committed).hexdigest() != expected.get(key):
                errors.append(name + ":main_blob_hash_mismatch:" + key)
            else:
                main_blob_checks += 1

        result = read_json(result_path)
        start, end = result.get("window_start_ns"), result.get("window_end_ns")
        if type(start) is not int or type(end) is not int or end - start != 600_000_000:
            errors.append(name + ":invalid_window")
            continue

        events = read_jsonl(event_path)
        in_window = [
            row for row in events
            if row.get("event") == "typed_observation"
            and type(row.get("capture_ns")) is int
            and start <= row["capture_ns"] < end
        ]
        observation_rows = [row for row in events if row.get("event") == "observation"]
        obs_index = {}
        for row in observation_rows:
            key = (row.get("id"), row.get("step"), row.get("sequence"),
                   row.get("capture_ns"), row.get("frame_rgb_sha256"))
            obs_index.setdefault(key, []).append(row)

        values = {signal: [] for signal in SIGNALS}
        matched = 0
        for row in in_window:
            if row.get("schema") != "doom-typed-observation-v1":
                errors.append(name + ":unexpected_typed_observation_schema")
            signals = row.get("signals")
            if type(signals) is not dict:
                errors.append(name + ":signals_not_object")
                continue
            for signal in SIGNALS:
                item = signals.get(signal)
                if (type(item) is not dict or item.get("signal_id") != signal
                        or item.get("status") != "observed"
                        or type(item.get("value")) is not int
                        or type(item.get("sequence")) is not int
                        or item.get("sequence") != row.get("sequence")
                        or type(item.get("capture_ns")) is not int
                        or item.get("capture_ns") != row.get("capture_ns")
                        or item.get("binding") != row.get("pointer_binding")):
                    errors.append(name + ":invalid_" + signal + "_signal")
                    continue
                values[signal].append(item["value"])
            key = (row.get("id"), row.get("step"), row.get("sequence"),
                   row.get("capture_ns"), row.get("frame_rgb_sha256"))
            matches = obs_index.get(key, [])
            if len(matches) != 1:
                errors.append(name + ":typed_observation_frame_join_not_unique")
            elif not (base / "runtime" / Path(matches[0].get("image", "")).name).is_file():
                errors.append(name + ":observation_image_missing")
            else:
                matched += 1

        for signal, series in values.items():
            if len(series) != len(in_window):
                errors.append(name + ":incomplete_" + signal + "_series")
        cells.append({
            "cell": name,
            "arm": result.get("arm"),
            "window_ns": [start, end],
            "typed_observation_count": len(in_window),
            "observation_frame_joins": matched,
            "signal_values": values,
            "health_transition_count": sum(a != b for a, b in zip(values["health"], values["health"][1:])),
            "ammo_transition_count": sum(a != b for a, b in zip(values["ammo"], values["ammo"][1:])),
        })

    return {
        "audit": "PASS_TYPED_STATE_SERIES_RECONCILED" if not errors else "FAIL",
        "checks": {
            "errors": errors,
            "cells": len(cells),
            "main_blob_checks": main_blob_checks,
            "typed_observations": sum(row["typed_observation_count"] for row in cells),
            "observation_frame_joins": sum(row["observation_frame_joins"] for row in cells),
            "health_transitions": sum(row["health_transition_count"] for row in cells),
            "ammo_transitions": sum(row["ammo_transition_count"] for row in cells),
        },
        "cells": cells,
        "scope": "Typed HUD health/ammo rows within the exact retained 600 ms windows, joined to the same-run observation metadata and saved screenshot paths; no OCR re-extraction, scorer claim, causal effect, useful-progress, physical-input, or live-control claim.",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--freeze", required=True, type=Path)
    parser.add_argument("--auditor", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    result = audit(args.root, read_json(args.freeze), args.auditor)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"audit": result["audit"], "checks": result["checks"]}, sort_keys=True))
    raise SystemExit(0 if result["audit"] != "FAIL" else 1)
