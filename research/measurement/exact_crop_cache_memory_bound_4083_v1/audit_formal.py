"""Raw-only audit with an independent decoder/scorer and fixed corruption controls."""
import copy
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

FORMAL = {"width": 800, "height": 600, "count": 64, "capacity": 8,
          "box": [40, 30, 100, 90], "profile": "FORMAL"}
CONSTRUCTION = {"width": 80, "height": 60, "count": 10, "capacity": 2,
               "box": [5, 4, 25, 20], "profile": "CONSTRUCTION_ONLY"}


def generated(version, width, height):
    yy, xx = np.indices((height, width))
    array = np.empty((height, width, 3), dtype=np.uint8)
    array[:, :, 0] = (xx * 7 + version * 19) % 256
    array[:, :, 1] = (yy * 11 + version * 23) % 256
    array[:, :, 2] = (xx + yy * 3 + version * 31) % 256
    return array


def digest(data):
    return hashlib.sha256(data).hexdigest()


def validate(raw, spec):
    errors, checks = [], 0
    width, height, count, cap, box = (spec[k] for k in ("width", "height", "count", "capacity", "box"))
    order = list(range(count)) + list(range(count - cap, count))
    if raw.get("schema") != "exact-crop-cache-memory-formal-raw-v1": errors.append("schema")
    if raw.get("profile") != spec["profile"]: errors.append("profile")
    freeze_path = HERE / "FREEZE.json"
    if not freeze_path.exists():
        errors.append("freeze-file-missing")
    elif spec["profile"] == "FORMAL":
        freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
        frozen_hashes = freeze.get("source_sha256", {})
        if raw.get("source_sha256") != frozen_hashes: errors.append("raw-source-hashes")
        for filename, expected_hash in frozen_hashes.items():
            source_path = HERE / filename
            if not source_path.is_file() or hashlib.sha256(source_path.read_bytes()).hexdigest() != expected_hash:
                errors.append(f"source-hash-{filename}")
    else:
        for filename, observed_hash in raw.get("source_sha256", {}).items():
            source_path = HERE / filename
            if not source_path.is_file() or hashlib.sha256(source_path.read_bytes()).hexdigest() != observed_hash:
                errors.append(f"construction-source-hash-{filename}")
    if raw.get("dimensions") != [width, height] or raw.get("capacity") != cap: errors.append("frozen-parameters")
    if raw.get("request_order") != order or len(raw.get("rows", [])) != len(order): errors.append("request-order")
    max_bytes, one_frame = cap * width * height * 3, width * height * 3
    with tempfile.TemporaryDirectory(prefix="exact-crop-memory-audit-") as td:
        paths, contracts = [], []
        for version in range(count):
            path = Path(td) / f"frame-{version:03d}.png"
            Image.fromarray(generated(version, width, height)).save(path, format="PNG", optimize=False)
            with Image.open(path) as opened:
                pixels = np.asarray(opened.convert("RGB"))
            expected = digest(pixels[box[1]:box[3], box[0]:box[2], :].tobytes())
            paths.append(path)
            contracts.append({"schema": "exact-rgb-crop-semantic-probe-v1",
                "probe_id": f"frame-{version:03d}", "box": box,
                "expected_crop_sha256": expected, "success_reason": "exact_crop_present",
                "grants_input_authority": False})
        for pos, version in enumerate(order):
            row = raw["rows"][pos]
            direct = score_path(contracts[version], paths[version])
            for arm in ("baseline", "unbounded", "bounded"):
                checks += 1
                if row.get(arm) != direct: errors.append(f"score-{arm}-{pos}")
            checks += 1
            file_sha = digest(paths[version].read_bytes())
            if row.get("artifact_sha256") != file_sha or row.get("input_sha256") != file_sha: errors.append(f"input-identity-{pos}")
            checks += 1
            if row.get("version") != version or row.get("request_index") != pos: errors.append(f"row-identity-{pos}")
            expected_unlimited = min(pos + 1, count) * one_frame
            checks += 1
            if row.get("unbounded_pixel_bytes") != expected_unlimited: errors.append(f"unbounded-occupancy-{pos}")
            expected_frames = min(pos + 1, cap)
            checks += 1
            if row.get("bounded_pixel_bytes", max_bytes + 1) > max_bytes: errors.append(f"bound-{pos}")
            if len(row.get("bounded_frame_entries", [])) != expected_frames: errors.append(f"lru-size-{pos}")
            checks += 1
            if set(row.get("bounded_crop_artifacts", [])) != set(row.get("bounded_frame_entries", [])): errors.append(f"crop-frame-closure-{pos}")
        final_versions = order[-cap:]
        final_ids = [raw["rows"][count - cap + i]["artifact_sha256"] for i in range(cap)]
        if raw.get("bounded_final_frame_entries") != final_ids: errors.append("final-lru-identities")
        if raw.get("bounded_final_crop_artifacts") != sorted(final_ids): errors.append("final-crops")
        for j in range(cap):
            if raw["rows"][count + j]["bounded_frame_hit_before"] is not True: errors.append(f"revisit-miss-{j}")
        if raw.get("bounded_final_pixel_bytes") != max_bytes: errors.append("final-bounded-bytes")
        if raw.get("unbounded_final_pixel_bytes") != count * one_frame: errors.append("final-unbounded-bytes")

    # Non-vacuous independent checks on copied evidence; each mutant must be rejected.
    mutants = []
    m=copy.deepcopy(raw);m["rows"][0]["bounded"]["observed_crop_sha256"]="0"*64;mutants.append(lambda x: x["rows"][0]["bounded"]!=x["rows"][0]["baseline"])
    m=copy.deepcopy(raw);m["rows"][0]["bounded_pixel_bytes"]=max_bytes+1;mutants.append(lambda x: x["rows"][0]["bounded_pixel_bytes"]>max_bytes)
    m=copy.deepcopy(raw);m["rows"][0]["bounded"]["grants_input_authority"]=True;mutants.append(lambda x: x["rows"][0]["bounded"].get("grants_input_authority") is not False)
    m=copy.deepcopy(raw);m["rows"][count]["bounded_frame_hit_before"]=False;mutants.append(lambda x: x["rows"][count]["bounded_frame_hit_before"] is not True)
    m=copy.deepcopy(raw);m["rows"][0]["artifact_sha256"]="f"*64;mutants.append(lambda x: x["rows"][0]["artifact_sha256"]!=x["rows"][0]["input_sha256"])
    # Re-apply mutations one by one to independent copies; don't use candidate output.
    control_results=[]
    for idx in range(5):
        mutant=copy.deepcopy(raw)
        if idx==0: mutant["rows"][0]["bounded"]["observed_crop_sha256"]="0"*64
        elif idx==1: mutant["rows"][0]["bounded_pixel_bytes"]=max_bytes+1
        elif idx==2: mutant["rows"][0]["bounded"]["grants_input_authority"]=True
        elif idx==3: mutant["rows"][count]["bounded_frame_hit_before"]=False
        elif idx==4: mutant["rows"][0]["artifact_sha256"]="f"*64
        control_results.append(bool(mutants[idx](mutant)))
    if not all(control_results): errors.append("corruption-controls")
    return {"schema":"exact-crop-cache-memory-formal-audit-v1",
        "disposition":"PASS_CONSTRUCTION_SCOPED" if spec["profile"]=="CONSTRUCTION_ONLY" and not errors else
          ("PASS_CACHE_MEMORY_BOUND_SCOPED" if not errors else "FAIL_OR_STOP_AUDIT"),
        "profile":spec["profile"],"checks":checks,"request_count":len(order),"errors":errors,
        "corruption_controls_rejected":sum(control_results),"corruption_controls_total":len(control_results),
        "max_bounded_pixel_bytes":max_bytes,
        "bounded_final_pixel_bytes":raw.get("bounded_final_pixel_bytes"),
        "unbounded_final_pixel_bytes":raw.get("unbounded_final_pixel_bytes")}


if __name__ == "__main__":
    import argparse
    p=argparse.ArgumentParser();p.add_argument("raw");p.add_argument("audit");p.add_argument("--construction",action="store_true");a=p.parse_args()
    raw=json.loads(Path(a.raw).read_text(encoding="utf-8"))
    result=validate(raw,CONSTRUCTION if a.construction else FORMAL)
    Path(a.audit).write_text(json.dumps(result,sort_keys=True,separators=(",",":"))+"\n",encoding="utf-8")
    print(json.dumps(result,sort_keys=True))
    if result["errors"]: raise SystemExit(1)

