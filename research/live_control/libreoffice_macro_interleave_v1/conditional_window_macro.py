import json
import time
from pathlib import Path


def apply_window(doc, name, expected_x, new_x, barrier_path, sleep_ms):
    page = doc.getDrawPages().getByIndex(0)
    shape = None
    for i in range(page.getCount()):
        candidate = page.getByIndex(i)
        if getattr(candidate, "Name", "") == name:
            shape = candidate
            break
    if shape is None:
        return json.dumps({"status": "MISSING"}, sort_keys=True)

    before_x = int(shape.getPosition().X)
    validation_ns = time.monotonic_ns()
    if before_x != int(expected_x):
        return json.dumps({
            "status": "REFUSED",
            "before_x": before_x,
            "validation_ns": validation_ns,
        }, sort_keys=True)

    Path(barrier_path).write_text(
        json.dumps({"validation_ns": validation_ns, "before_x": before_x}, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    time.sleep(int(sleep_ms) / 1000.0)

    prewrite_x = int(shape.getPosition().X)
    prewrite_ns = time.monotonic_ns()
    pos = shape.getPosition()
    pos.X = int(new_x)
    set_start_ns = time.monotonic_ns()
    shape.setPosition(pos)
    set_end_ns = time.monotonic_ns()
    after_x = int(shape.getPosition().X)
    return json.dumps({
        "status": "APPLIED",
        "before_x": before_x,
        "prewrite_x": prewrite_x,
        "after_x": after_x,
        "validation_ns": validation_ns,
        "prewrite_ns": prewrite_ns,
        "set_start_ns": set_start_ns,
        "set_end_ns": set_end_ns,
    }, sort_keys=True)


g_exportedScripts = (apply_window,)
