"""Audit strict model-authored displacement conditions on retained frame pairs."""
import hashlib
import json
import os
from pathlib import Path

import numpy as np
from PIL import Image

from local_displacement_postcondition_v1 import LocalDisplacementPostcondition
from parse_local_displacement_author_v1 import parse


HERE = Path(__file__).resolve().parent
ROOT = HERE / "results/local-displacement-authorship-01"
FRAMES = HERE / "results/local-displacement-x11-02"


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def local_path(value):
    value = str(value)
    if os.name != "nt" and len(value) >= 3 and value[1:3] == ":\\":
        return Path("/mnt") / value[0].lower() / value[3:].replace("\\", "/")
    return Path(value)


def image(path):
    with Image.open(path) as opened:
        return np.asarray(opened.convert("RGB"))


def message_and_usage(path):
    rows = [json.loads(line) for line in Path(path).read_text().splitlines()]
    messages = [row["item"]["text"] for row in rows
                if row.get("type") == "item.completed" and row.get("item", {}).get("type") == "agent_message"]
    usages = [row["usage"] for row in rows if row.get("type") == "turn.completed"]
    assert len(messages) == len(usages) == 1
    return messages[0], usages[0]


def observation_images(directory, sequences):
    rows = [json.loads(line) for line in (directory / "events.jsonl").read_text().splitlines()]
    by_sequence = {row["sequence"]: row for row in rows if row.get("event") == "observation"}
    return [image(directory / Path(by_sequence[sequence]["image"]).name) for sequence in sequences]


def apply(spec, samples, sequences):
    source = image(FRAMES / "target/001.png")
    condition = LocalDisplacementPostcondition(spec, source, 1, "inkscape-window")
    return condition.evaluate(samples, sequences, ["inkscape-window"] * 2,
                              [1_000_000_000, 1_050_000_000])


def main():
    plan = read(ROOT / "preregistration.json")
    assert plan["status"] == "preregistered_before_model_execution"
    for name, expected in plan["sources"].items():
        assert sha(HERE / name) == expected, name
    assert sha(local_path(plan["image"])) == plan["image_sha256"]
    assert sha(ROOT / "prompt.txt") == plan["prompt_sha256"]
    execution = read(ROOT / "execution.json")
    assert [row["name"] for row in execution] == plan["order"]
    assert all(row["exit_code"] == 0 and row["stderr"] == "" for row in execution)
    target_samples = observation_images(FRAMES / "target", [7, 8])
    partial_samples = observation_images(FRAMES / "partial", [8, 9])
    red = [596, 373, 643, 408]
    cases = []
    for execution_row in execution:
        directory = ROOT / execution_row["name"]
        text, usage = message_and_usage(directory / "events.jsonl")
        spec = parse(text)
        target = apply(spec, target_samples, [7, 8])
        partial = apply(spec, partial_samples, [8, 9])
        x, y, width, height = spec["box"]
        intersection = max(0, min(x + width, red[2]) - max(x, red[0])) * \
            max(0, min(y + height, red[3]) - max(y, red[1]))
        red_area = (red[2] - red[0]) * (red[3] - red[1])
        passed = target["reason"] == "met" and partial["reason"] != "met"
        cases.append({
            "name": execution_row["name"], "route": execution_row["route"],
            "spec": spec, "target": target, "partial": partial,
            "red_bbox_coverage": intersection / red_area,
            "strict_primary_pass": passed, "usage": usage,
            "runner_wall_ms": execution_row["duration_ns"] / 1e6,
        })
    routes = {}
    for route in plan["routes"]:
        selected = [case for case in cases if case["route"] == route]
        routes[route] = {
            "strict_primary_passes": sum(case["strict_primary_pass"] for case in selected),
            "calls": len(selected),
            "input_tokens": sum(case["usage"]["input_tokens"] for case in selected),
            "cached_input_tokens": sum(case["usage"]["cached_input_tokens"] for case in selected),
            "output_tokens": sum(case["usage"]["output_tokens"] for case in selected),
            "runner_wall_ms": [case["runner_wall_ms"] for case in selected],
        }
    assert routes["luna"]["strict_primary_passes"] == 2
    assert routes["astra"]["strict_primary_passes"] == 2
    report = {
        "audit_passed": True, "preregistered": True, "cases": cases, "routes": routes,
        "all_strict_json": True, "all_boxes_cover_full_red_bbox": all(case["red_bbox_coverage"] == 1 for case in cases),
        "decision": "ADVANCE_AUTHORSHIP_SIGNAL_TO_FRESH_LIVE_ALLOCATION;_NO_PROMOTION",
        "limits": "four fixed-context calls on one source image and retained effect pairs; prompt fixed most contract fields; no live model-controlled input, speed comparison, population, cross-domain or generalization claim",
        "audit_sha256": sha(Path(__file__)),
    }
    (ROOT / "audit.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
