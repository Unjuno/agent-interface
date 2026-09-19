"""Create meaning-free receipts for persistent OpenTTD hover tooltips."""
import hashlib
from pathlib import Path

from PIL import Image


TOOLTIP_COLOR = (252, 248, 128)


def tooltip(image_or_path):
    if isinstance(image_or_path, Image.Image):
        image = image_or_path.convert("RGB")
    else:
        with Image.open(Path(image_or_path)) as opened:
            image = opened.convert("RGB")
    pixels = image.load()
    remaining = {(x, y) for y in range(60, min(145, image.height))
                 for x in range(image.width) if pixels[x, y] == TOOLTIP_COLOR}
    components = []
    while remaining:
        stack = [remaining.pop()]
        found = []
        while stack:
            x, y = stack.pop()
            found.append((x, y))
            for neighbour in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
                if neighbour in remaining:
                    remaining.remove(neighbour)
                    stack.append(neighbour)
        components.append(found)
    if not components:
        raise ValueError("tooltip yellow region missing")
    points = max(components, key=len)
    if len(points) < 400:
        raise ValueError("tooltip yellow region too small")
    box = [min(x for x, _ in points), min(y for _, y in points),
           max(x for x, _ in points) + 1, max(y for _, y in points) + 1]
    crop = image.crop(tuple(box))
    return {"box": box, "size": list(crop.size), "yellow_pixels": len(points),
            "pixels_sha256": hashlib.sha256(crop.tobytes()).hexdigest()}


def verify(records, steps, points, runtime_dir):
    expected = []
    for x, y in points:
        expected += [{"op": "pointer_move", "x": x, "y": y},
                     {"op": "dwell_observe", "delay_ms": 800},
                     {"op": "observe"}]
    if steps != expected:
        raise ValueError("hover program does not match proposed points")
    admissions = [row for row in records if row.get("event") == "pointer_admission"]
    if [(row.get("step"), row.get("operation"), row.get("payload")) for row in admissions] != [
            (index * 3, "move", {"x": point[0], "y": point[1]})
            for index, point in enumerate(points)]:
        raise ValueError("pointer admissions do not bind proposed points")
    observations = {row["step"]: row for row in records if row.get("event") == "observation"}
    binding = None
    receipts = []
    for index, point in enumerate(points):
        dwell = observations.get(index * 3 + 1)
        persistent = observations.get(index * 3 + 2)
        if dwell is None or persistent is None:
            raise ValueError("dwell and persistence observations required")
        for observation in (dwell, persistent):
            if observation.get("focus_samples_match") is not True:
                raise ValueError("focus samples changed during hover evidence")
            if binding is None:
                binding = observation.get("pointer_binding")
            elif observation.get("pointer_binding") != binding:
                raise ValueError("pointer binding changed during hover evidence")
        first = tooltip(Path(runtime_dir) / Path(dwell["image"]).name)
        second = tooltip(Path(runtime_dir) / Path(persistent["image"]).name)
        if first != second:
            raise ValueError("tooltip did not persist exactly")
        receipts.append({"receipt_index": index + 1, "point": point,
                         "dwell_sequence": dwell["sequence"],
                         "persistent_sequence": persistent["sequence"],
                         "tooltip": first,
                         "authority": "observation evidence only; grants no input authority"})
    return {"status": "READY", "binding": binding, "receipts": receipts}
