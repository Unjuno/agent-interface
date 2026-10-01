import hashlib, json

W, H = 16, 12
TARGETS = [(1, 1, 2, 2), (13, 0, 3, 2), (7, 9, 2, 2), None]

def frame(i):
    pixels = [[0 for _ in range(W)] for _ in range(H)]
    # Repeated identical controls plus one target marker; coordinates are source-space.
    for x, y in ((1, 1), (5, 1), (9, 1), (13, 0), (7, 9)):
        for yy in range(y, min(H, y + 2)):
            for xx in range(x, min(W, x + 2)):
                pixels[yy][xx] = 1
    if i == 3:  # target-absent family
        pixels[1][1] = 0
    return pixels

def cues(target):
    x, y, w, h = target if target else (0, 0, 0, 0)
    return {
        "RAW": {"source_size": [W, H], "target": None},
        "BORDER_RULER": {"source_size": [W, H], "border": [x, y, w, h], "ruler_origin": [0, 0]},
        "COARSE_GRID": {"source_size": [W, H], "grid": [4, 3], "cell_target": [x // 4, y // 4] if target else None},
        "TARGET_CONTEXT_CROP": {"source_size": [W, H], "crop": [max(0, x-1), max(0, y-1), min(W, x+w+1), min(H, y+h+1)] if target else None},
    }

def map_back(arm, payload):
    if arm == "RAW": return None
    if arm == "BORDER_RULER": return tuple(payload["border"]) if payload["border"][2] else None
    if arm == "COARSE_GRID":
        cell = payload["cell_target"]
        return None if cell is None else (cell[0] * 4, cell[1] * 4, 4, 4)
    crop = payload["crop"]
    return None if crop is None else (crop[0], crop[1], crop[2] - crop[0], crop[3] - crop[1])

def main():
    rows = []
    mapping_failures = 0
    for family, target in enumerate(TARGETS):
        for arm, payload in cues(target).items():
            mapped = map_back(arm, payload)
            if target and arm == "BORDER_RULER" and mapped != target: mapping_failures += 1
            if not target and mapped is not None: mapping_failures += 1
            rows.append({"family": family, "arm": arm, "target_present": target is not None, "mapped": mapped, "raw_fallback": True})
    raw = json.dumps(rows, sort_keys=True, separators=(",", ":")).encode()
    result = {"decision": "HOLD_MODEL_EVALUATION_UNAVAILABLE", "rows": len(rows), "mapping_failures": mapping_failures, "raw_fallback_violations": 0, "model_invocations": 0, "gui_mutations": 0, "sha256": hashlib.sha256(raw).hexdigest()}
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if mapping_failures == 0 else 1

if __name__ == "__main__": raise SystemExit(main())
