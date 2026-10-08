from __future__ import annotations

import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
WIDTH, HEIGHT = 16, 12
CAPTURE_NS = 300_000
CRITICAL = [[15, 2]]


def background():
    return [[20 + ((x * 17 + y * 31 + (x * y) % 7) % 221)
             for x in range(WIDTH)] for y in range(HEIGHT)]


def shift(frame, dx):
    return [[frame[y][x - dx] if 0 <= x - dx < WIDTH else 0
             for x in range(WIDTH)] for y in range(HEIGHT)]


def paint(frame, x, y, value=255):
    frame[y][x] = value


def receipt(intent, action, support, status="delivered", *, ack_ns=150_000,
            viewport_generation=7, focus_generation=4):
    return {"receipt_id": f"receipt-{intent}", "intent_id": intent,
            "action": action, "allowed_dx": support, "delivery_status": status,
            "request_ns": 100_000, "ack_ns": ack_ns, "release_ns": 400_000,
            "viewport_generation": viewport_generation,
            "focus_generation": focus_generation}


def build_case(case_id, dx, *, support=None, intent=None, status="delivered",
               ack_ns=150_000, viewport_generation=7, focus_generation=4,
               event=None, variant=None, receipt_present=True):
    prev = background()
    current = shift(prev, dx)
    if variant == "parallax":
        for y in range(3, 9):
            for x in range(8, 15):
                current[y][x] = current[y][x - 1] if x > 8 else 0
    elif variant == "nonrigid":
        for y in range(5, 8):
            for x in range(4, 12):
                current[y][x] = min(255, current[y][x] + (13 if (x + y) % 2 else 0))
    elif variant == "occlusion":
        for y in range(4, 8):
            for x in range(6, 10):
                current[y][x] = 0
    if event == "flash":
        paint(current, 5, 9)
    elif event == "moving_object":
        for y in (8, 9):
            for x in (12, 13):
                paint(current, x, y)
    elif event == "critical_cue":
        paint(current, 15, 2)
    current_intent = intent or f"intent-{case_id}"
    active = receipt(current_intent, "pan_right" if support != [0] else "no_input",
                     support if support is not None else [dx], status,
                     ack_ns=ack_ns, viewport_generation=viewport_generation,
                     focus_generation=focus_generation) if receipt_present else None
    # This deliberately valid-looking receipt belongs to a different intent.
    sham = receipt("foreign-sham-intent", "no_input", [0])
    return ({"case_id": case_id, "intent_id": current_intent,
             "capture_ns": CAPTURE_NS, "viewport_generation": 7,
             "focus_generation": 4, "width": WIDTH, "height": HEIGHT,
             "critical_pixels": CRITICAL, "previous": prev, "current": current,
             "receipt": active, "sham_receipt": sham},
            {"case_id": case_id, "events": ([] if event is None else
             [{"event_id": f"{case_id}-{event}", "kind": event,
               "x": 15 if event == "critical_cue" else (5 if event == "flash" else 12),
               "y": 2 if event == "critical_cue" else (9 if event == "flash" else 8),
               "onset_ns": 250_000, "deadline_ns": 350_000,
               "critical": event == "critical_cue"}])})


def main():
    specs = [
        ("clean_pan_2", 2, {"support": [2]}),
        ("clean_pan_3", 3, {"support": [3]}),
        ("pan_tiny_flash", 2, {"support": [2], "event": "flash"}),
        ("pan_moving_object", 2, {"support": [2], "event": "moving_object"}),
        ("pan_critical_cue", 2, {"support": [2], "event": "critical_cue"}),
        ("under_delivery_interval", 1, {"support": [1, 2, 3]}),
        ("over_delivery_interval", 3, {"support": [1, 2]}),
        ("late_delivery_flash", 2, {"support": [2], "ack_ns": 350_000, "event": "flash"}),
        ("failed_delivery_flash", 0, {"support": [2], "status": "failed", "ack_ns": None, "event": "flash"}),
        ("external_scroll_no_receipt", 2, {"receipt_present": False}),
        ("pan_parallax", 2, {"support": [2], "variant": "parallax"}),
        ("pan_nonrigid", 2, {"support": [2], "variant": "nonrigid"}),
        ("stale_viewport_occlusion", 2, {"support": [2], "variant": "occlusion", "viewport_generation": 6}),
        ("stale_focus", 2, {"support": [2], "focus_generation": 3}),
        ("no_input_unchanged", 0, {"support": [0]}),
        ("out_of_envelope_motion", 4, {"support": [2]}),
    ]
    inputs, ledger = [], []
    for case_id, dx, options in specs:
        row, truth = build_case(case_id, dx, **options)
        inputs.append(row)
        ledger.append(truth)
    (HERE / "fixture").mkdir(exist_ok=True)
    (HERE / "fixture" / "inputs.json").write_text(
        json.dumps({"schema": "action-bound-residual-input-v1", "cases": inputs},
                   sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    (HERE / "fixture" / "oracle.json").write_text(
        json.dumps({"schema": "action-bound-residual-oracle-v1", "cases": ledger},
                   sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    print(f"PASS_FIXTURE cases={len(inputs)} scheduled_events={sum(len(x['events']) for x in ledger)}")


if __name__ == "__main__":
    main()
