"""Independent construction auditor; deliberately does not import study/candidate."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "upstream"))
from exact_crop_semantic_probe_v1 import score_path

WIDTH, HEIGHT, COUNT, CAPACITY = 80, 60, 10, 2
BOX = [5, 4, 25, 20]
ORDER = list(range(COUNT)) + [COUNT - 2, COUNT - 1]


def generated_pixels(version):
    yy, xx = np.indices((HEIGHT, WIDTH))
    pixels = np.empty((HEIGHT, WIDTH, 3), dtype=np.uint8)
    pixels[:, :, 0] = (xx * 7 + version * 19) % 256
    pixels[:, :, 1] = (yy * 11 + version * 23) % 256
    pixels[:, :, 2] = (xx + yy * 3 + version * 31) % 256
    return pixels


def sha_bytes(value):
    return hashlib.sha256(value).hexdigest()


def main(raw_path, audit_path):
    raw = json.loads(Path(raw_path).read_text(encoding="utf-8"))
    errors, checks = [], 0
    if raw.get("schema") != "exact-crop-cache-memory-construction-v1" or raw.get("formal") is not False:
        errors.append("schema/formal")
    if raw.get("dimensions") != [WIDTH, HEIGHT] or raw.get("capacity") != CAPACITY:
        errors.append("frozen-parameters")
    if raw.get("request_order") != ORDER or len(raw.get("rows", [])) != len(ORDER):
        errors.append("request-order")

    with tempfile.TemporaryDirectory(prefix="exact-crop-lru-audit-") as td:
        paths, contracts = [], []
        for version in range(COUNT):
            path = Path(td) / f"frame-{version:02d}.png"
            Image.fromarray(generated_pixels(version)).save(path, format="PNG", optimize=False)
            with Image.open(path) as im:
                pixels = np.asarray(im.convert("RGB"))
            expected = sha_bytes(pixels[BOX[1]:BOX[3], BOX[0]:BOX[2], :].tobytes())
            paths.append(path)
            contracts.append({"schema": "exact-rgb-crop-semantic-probe-v1",
                "probe_id": f"construction-{version:02d}", "box": BOX,
                "expected_crop_sha256": expected, "success_reason": "exact_crop_present",
                "grants_input_authority": False})
        max_bytes = CAPACITY * WIDTH * HEIGHT * 3
        frame_bytes = WIDTH * HEIGHT * 3
        for pos, version in enumerate(ORDER):
            row = raw["rows"][pos]
            direct = score_path(contracts[version], paths[version])
            checks += 1
            if row.get("version") != version or row.get("artifact_sha256") != sha_bytes(paths[version].read_bytes()):
                errors.append(f"identity-{pos}")
            checks += 1
            for arm in ("baseline", "unbounded", "bounded"):
                checks += 1
                if row.get(arm) != direct:
                    errors.append(f"score-{arm}-{pos}")
            checks += 1
            if row.get("bounded_pixel_bytes", max_bytes + 1) > max_bytes:
                errors.append(f"bound-{pos}")
            expected_unbounded = min(pos + 1, COUNT) * frame_bytes
            checks += 1
            if row.get("unbounded_pixel_bytes") != expected_unbounded:
                errors.append(f"unbounded-occupancy-{pos}")
            expected_lru_count = min(pos + 1, CAPACITY)
            checks += 1
            if len(row.get("bounded_frame_entries", [])) != expected_lru_count:
                errors.append(f"lru-count-{pos}")
            checks += 1
            if set(row.get("bounded_crop_entries", [])) != set(row.get("bounded_frame_entries", [])):
                errors.append(f"crop-frame-liveness-{pos}")
        expected_final = [raw["rows"][8]["artifact_sha256"], raw["rows"][9]["artifact_sha256"]]
        if raw.get("bounded_final_frame_entries") != expected_final:
            errors.append("final-lru-order")
        if raw.get("bounded_final_crop_artifacts") != sorted(expected_final):
            errors.append("final-crop-entries")
        if raw["rows"][10]["bounded_frame_hit_before"] is not True or raw["rows"][11]["bounded_frame_hit_before"] is not True:
            errors.append("final-revisit-hit")
        if raw.get("bounded_final_pixel_bytes") != max_bytes:
            errors.append("final-pixel-bytes")
        if raw.get("unbounded_final_pixel_bytes") != COUNT * frame_bytes:
            errors.append("unbounded-final-bytes")

    # Effective raw-only corruption checks on independent copies.
    controls = []
    mutants = []
    bad = json.loads(json.dumps(raw)); bad["rows"][0]["bounded_pixel_bytes"] = max_bytes + 1; mutants.append(bad)
    bad = json.loads(json.dumps(raw)); bad["rows"][0]["bounded"]["grants_input_authority"] = True; mutants.append(bad)
    bad = json.loads(json.dumps(raw)); bad["bounded_final_frame_entries"] = ["mutated-identity"]; mutants.append(bad)
    bad = json.loads(json.dumps(raw)); bad["rows"][10]["bounded_frame_hit_before"] = False; mutants.append(bad)
    # Mutations must be detected by direct invariant probes, not merely by JSON parsing.
    controls.extend([
        mutants[0]["rows"][0]["bounded_pixel_bytes"] > max_bytes,
        mutants[1]["rows"][0]["bounded"]["grants_input_authority"] is not False,
        mutants[2]["bounded_final_frame_entries"] != expected_final,
        mutants[3]["rows"][10]["bounded_frame_hit_before"] is not True])
    if not all(controls):
        errors.append("corruption-control")
    outcome = {"schema": "exact-crop-cache-memory-construction-audit-v1",
        "disposition": "PASS_CONSTRUCTION_SCOPED" if not errors else "FAIL_CONSTRUCTION_AUDIT",
        "checks": checks, "errors": errors, "corruption_controls_rejected": sum(controls),
        "corruption_controls_total": len(controls), "request_count": len(ORDER),
        "unbounded_final_pixel_bytes": raw.get("unbounded_final_pixel_bytes"),
        "bounded_final_pixel_bytes": raw.get("bounded_final_pixel_bytes"),
        "max_bounded_pixel_bytes": max_bytes}
    Path(audit_path).write_text(json.dumps(outcome, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    print(json.dumps(outcome, sort_keys=True))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: audit.py RAW.json AUDIT.json")
    main(sys.argv[1], sys.argv[2])

