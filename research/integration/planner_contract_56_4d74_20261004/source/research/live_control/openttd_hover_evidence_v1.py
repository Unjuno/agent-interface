"""Verify fixed OpenTTD hover candidates before planner presentation."""
import hashlib
from pathlib import Path

from PIL import Image


TOOLTIP_COLOR = (252, 248, 128)
CANDIDATES = {
    "subsidies": {
        "point": [432, 51],
        "tooltip_size": [94, 12],
        "tooltip_sha256": "24f16a6512cf722fd630e0df7e520a83f37afc79628728596640f75c94dfe292",
        "meaning": "Display subsidies",
    },
    "trains": {
        "point": [650, 51],
        "tooltip_size": [198, 32],
        "tooltip_sha256": "e3263ffdb7b6fa63ff7301eb8e2cfcd742f042a10cf4cc9550aebdaee4bce593",
        "meaning": "Display list of company's trains",
    },
    "roads": {
        "point": [820, 51],
        "tooltip_size": [62, 12],
        "tooltip_sha256": "a59e729851367b2be8a7d21f82f7d24e8879eb06cadab12eb60261d3b36df581",
        "meaning": "Build roads",
    },
}
ORDER = ["subsidies", "trains", "roads"]


def _component(image):
    pixels = image.load()
    remaining = {
        (x, y) for y in range(60, min(130, image.height))
        for x in range(image.width) if pixels[x, y] == TOOLTIP_COLOR
    }
    components = []
    while remaining:
        stack = [remaining.pop()]
        found = []
        while stack:
            point = stack.pop()
            found.append(point)
            x, y = point
            for neighbour in ((x - 1, y), (x + 1, y),
                              (x, y - 1), (x, y + 1)):
                if neighbour in remaining:
                    remaining.remove(neighbour)
                    stack.append(neighbour)
        components.append(found)
    if not components:
        raise ValueError("tooltip yellow region missing")
    points = max(components, key=len)
    if len(points) < 400:
        raise ValueError("tooltip yellow region too small")
    left = min(x for x, _ in points)
    top = min(y for _, y in points)
    right = max(x for x, _ in points) + 1
    bottom = max(y for _, y in points) + 1
    return [left, top, right, bottom], len(points)


def classify(image_or_path):
    if isinstance(image_or_path, Image.Image):
        image = image_or_path.convert("RGB")
    else:
        with Image.open(image_or_path) as opened:
            image = opened.convert("RGB")
    box, yellow_pixels = _component(image)
    crop = image.crop(tuple(box))
    digest = hashlib.sha256(crop.tobytes()).hexdigest()
    size = list(crop.size)
    matches = [name for name, spec in CANDIDATES.items()
               if spec["tooltip_size"] == size
               and spec["tooltip_sha256"] == digest]
    if len(matches) != 1:
        raise ValueError("tooltip is not one preregistered readable template")
    return {"candidate_id": matches[0], "point": CANDIDATES[matches[0]]["point"],
            "meaning": CANDIDATES[matches[0]]["meaning"], "box": box,
            "yellow_pixels": yellow_pixels, "tooltip_sha256": digest}


def verify(records, steps, runtime_dir, declared_order=None):
    order = ORDER if declared_order is None else declared_order
    if (type(order) is not list or len(order) != 3
            or len(set(order)) != 3 or any(name not in CANDIDATES for name in order)):
        raise ValueError("three unique declared candidates required")
    expected_steps = []
    for name in order:
        x, y = CANDIDATES[name]["point"]
        expected_steps.extend([
            {"op": "pointer_move", "x": x, "y": y},
            {"op": "dwell_observe", "delay_ms": 800},
            {"op": "observe"},
        ])
    if steps != expected_steps:
        raise ValueError("hover program does not match declared candidate order")
    admissions = [row for row in records if row.get("event") == "pointer_admission"]
    if [(row.get("step"), row.get("operation"), row.get("payload"))
            for row in admissions] != [
                (index * 3, "move", {"x": CANDIDATES[name]["point"][0],
                                      "y": CANDIDATES[name]["point"][1]})
                for index, name in enumerate(order)]:
        raise ValueError("pointer admissions do not bind declared candidates")
    observations = {row["step"]: row for row in records
                    if row.get("event") == "observation"}
    evidence = []
    binding = None
    for index, name in enumerate(order):
        dwell = observations.get(index * 3 + 1)
        persistent = observations.get(index * 3 + 2)
        if dwell is None or persistent is None:
            raise ValueError("dwell and persistence observations required")
        for observation in (dwell, persistent):
            if observation.get("focus_samples_match") is not True:
                raise ValueError("focus samples changed during hover evidence")
            current = observation.get("pointer_binding")
            if binding is None:
                binding = current
            elif current != binding:
                raise ValueError("pointer binding changed during hover evidence")
        first = classify(Path(runtime_dir) / Path(dwell["image"]).name)
        second = classify(Path(runtime_dir) / Path(persistent["image"]).name)
        if first["candidate_id"] != name or second["candidate_id"] != name:
            raise ValueError("candidate-to-tooltip association mismatch")
        if first["tooltip_sha256"] != second["tooltip_sha256"]:
            raise ValueError("tooltip did not persist exactly")
        evidence.append({"candidate_id": name, "point": CANDIDATES[name]["point"],
                         "meaning": CANDIDATES[name]["meaning"],
                         "dwell_sequence": dwell["sequence"],
                         "persistent_sequence": persistent["sequence"],
                         "tooltip_box": first["box"],
                         "tooltip_sha256": first["tooltip_sha256"]})
    return {"status": "READY", "binding": binding, "evidence": evidence}
