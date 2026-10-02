"""Deterministic synthetic action-bound visual-residual candidate for Issue #6619."""
import json
import sys
from pathlib import Path


def blank(w, h, value=0):
    return [[value for _ in range(w)] for _ in range(h)]


def put(img, x, y, value):
    if 0 <= y < len(img) and 0 <= x < len(img[0]):
        img[y][x] = value


def shift(img, dx):
    out = blank(len(img[0]), len(img))
    for y, row in enumerate(img):
        for x, value in enumerate(row):
            put(out, x + dx, y, value)
    return out


def scene(case, frame):
    w = h = 32
    h = 24
    img = blank(w, h)
    for y in range(h):
        for x in range(w):
            if (x + 3 * y) % 11 == 0:
                img[y][x] = 20
    delivered = case["delivery"]
    actual_dx = {"exact": 2, "under": 1, "over": 3, "delayed": 0,
                 "failed": 0, "none": 0}[delivered]
    # Viewport pan is an actual delivered effect, not inferred from requested action.
    if frame == 0:
        img = blank(w, h)
        for y in range(h):
            for x in range(w):
                if (x + 3 * y) % 11 == 0:
                    img[y][x] = 20
    else:
        img = shift(img, actual_dx)
    event = case["event"]
    if frame == 1:
        if event in ("flash", "critical"):
            put(img, 16, 12, 255 if event == "flash" else 240)
        elif event == "external-scroll":
            put(img, 7, 4, 180)
        elif event in ("object", "parallax-critical", "nonrigid"):
            x = {"object": 10, "parallax-critical": 12, "nonrigid": 20}[event]
            val = 250 if event == "parallax-critical" else 90
            put(img, x, 8, val)
            if event == "nonrigid":
                put(img, x + 1, 8, val)
        elif event == "occluded-critical":
            # Intentionally absent in visible raster: oracle must report unobservable.
            pass
    return img


def translated(src, dx):
    out = blank(len(src[0]), len(src))
    for y, row in enumerate(src):
        for x, value in enumerate(row):
            put(out, x + dx, y, value)
    return out


def run(fixture):
    rows = []
    for case in fixture["cases"]:
        frames = [scene(case, 0), scene(case, 1)]
        receipt = {"requested": "pan" if case["delivery"] != "none" else "none",
                   "delivery": case["delivery"], "actual_dx": {"exact":2,"under":1,"over":3,"delayed":0,"failed":0,"none":0}[case["delivery"]],
                   "source_generation": case["generation"], "captured_generation": 1,
                   "valid": case["generation"] == 1 and case["delivery"] in ("exact","under","over")}
        predicted_dx = receipt["actual_dx"] if receipt["valid"] else 0
        predicted = translated(frames[0], predicted_dx)
        residual = [[int(a != b) for a, b in zip(ra, rb)] for ra, rb in zip(predicted, frames[1])]
        raw_delta = [[int(a != b) for a, b in zip(ra, rb)] for ra, rb in zip(frames[0], frames[1])]
        # Equal-budget alarm policy: prioritize high-contrast changed cells, deterministic row-major tie break.
        def alarm(mask, before, after):
            cells = [(abs(after[y][x] - before[y][x]), y, x) for y in range(len(mask))
                     for x in range(len(mask[0])) if mask[y][x]]
            cells.sort(key=lambda p: (-p[0], p[1], p[2]))
            out = [[0 for _ in mask[0]] for _ in mask]
            for _, y, x in cells[:fixture["alarm_budget_cells"]]:
                out[y][x] = 1
            return out
        arms = {
            "raw": alarm(raw_delta, frames[0], frames[1]),
            "agnostic": alarm(raw_delta, frames[0], frames[1]),
            "bound": alarm(residual, predicted, frames[1]),
            "sham": alarm([[int(a != b) for a, b in zip(ra, rb)] for ra, rb in zip(translated(frames[0], 2), frames[1])], predicted, frames[1]),
        }
        rows.append({"id":case["id"], "frames":frames, "receipt":receipt,
                     "predicted_frame":predicted, "predicted_dx":predicted_dx,
                     "residual_mask":residual, "alarms":arms})
    return {"schema":"action-bound-residual-raw-v1", "fixture_schema":fixture["schema"], "rows":rows}


def main(fixture_path, out_path):
    fixture = json.loads(Path(fixture_path).read_text(encoding="utf-8"))
    raw = run(fixture)
    Path(out_path).write_text(json.dumps(raw, sort_keys=True, separators=(",", ":"))+"\n", encoding="utf-8")
    print(json.dumps({"schema":raw["schema"],"rows":len(raw["rows"]),"output":str(out_path)},sort_keys=True))


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: candidate.py CASES.json RAW.json")
    main(*sys.argv[1:])
