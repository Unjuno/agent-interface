"""Frozen nine-case calibration for Issue #4083."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import sys
import time

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "upstream"))
import exact_crop_semantic_probe_v1 as upstream
from candidate import DependencyCache

W, H = 1024, 768
BOXES = ([96, 96, 224, 224], [320, 128, 448, 256], [560, 224, 688, 352], [736, 448, 864, 576])
WORKLOADS = ("METADATA", "ROI", "IMAGE")


def sha(data):
    return hashlib.sha256(data).hexdigest()


def make_fixture(index):
    y, x = np.indices((H, W), dtype=np.uint16)
    arr = np.empty((H, W, 3), dtype=np.uint8)
    arr[..., 0] = ((x + index * 17) % 251).astype(np.uint8)
    arr[..., 1] = ((2 * y + index * 31) % 253).astype(np.uint8)
    arr[..., 2] = ((x // 3 + y // 5 + index * 47) % 247).astype(np.uint8)
    # Bounded exact patches make crop identities visibly distinct while retaining deterministic images.
    for j, (l, t, r, b) in enumerate(BOXES):
        arr[t:b, l:r, :] = ((index * 41 + j * 53) % 256,
                             (index * 67 + j * 29) % 256,
                             (index * 13 + j * 97) % 256)
    return Image.fromarray(arr, "RGB")


def fixture_paths(root):
    root.mkdir(parents=True, exist_ok=True)
    paths = []
    for i in range(4):
        p = root / f"fixture-{i}.png"
        if not p.exists():
            make_fixture(i).save(p, format="PNG", compress_level=6)
        paths.append(p)
    return paths


def exact_crop_digest(path, box):
    with Image.open(path) as src:
        arr = np.asarray(src.convert("RGB"))
    l, t, r, b = box
    return sha(arr[t:b, l:r].tobytes())


def build_requests(workload, paths):
    digests = {(i, j): exact_crop_digest(paths[i], box)
               for i in range(4) for j, box in enumerate(BOXES)}
    rows = []
    for k in range(24):
        if workload == "METADATA":
            image_i, box_i = 0, 0
            expected = digests[(0, 0)] if k % 4 != 3 else "0" * 64
            reason = f"stable-semantic-{k % 3}"
        elif workload == "ROI":
            image_i, box_i = 1, k % 4
            expected = digests[(1, box_i)] if k % 5 else "f" * 64
            reason = "roi-check"
        else:
            image_i, box_i = k % 4, 2
            expected = digests[(image_i, 2)] if k % 6 != 5 else "a" * 64
            reason = "image-check"
        contract = {
            "schema": upstream.CONTRACT_SCHEMA,
            "probe_id": f"{workload.lower()}-{k:02d}",
            "box": list(BOXES[box_i]),
            "expected_crop_sha256": expected,
            "success_reason": reason,
            "grants_input_authority": False,
        }
        rows.append({"index": k, "image_index": image_i, "image": str(paths[image_i]), "contract": contract})
    return rows


def run_arm(arm, requests):
    cache = DependencyCache() if arm == "CANDIDATE" else None
    outputs = []
    w0, c0 = time.perf_counter_ns(), time.process_time_ns()
    for request in requests:
        rw0, rc0 = time.perf_counter_ns(), time.process_time_ns()
        if arm == "BASELINE":
            result = upstream.score_path(request["contract"], request["image"])
        else:
            result = cache.score(request["contract"], request["image"])
        outputs.append({
            "index": request["index"],
            "result": result,
            "wall_ns": time.perf_counter_ns() - rw0,
            "cpu_ns": time.process_time_ns() - rc0,
        })
    return {
        "arm": arm,
        "wall_ns": time.perf_counter_ns() - w0,
        "cpu_ns": time.process_time_ns() - c0,
        "outputs": outputs,
        "counters": None if cache is None else cache.counters,
    }


def run_case(workload, rep, out):
    fixture_root = HERE / "fixtures"
    paths = fixture_paths(fixture_root)
    requests = build_requests(workload, paths)
    # Prime exact source files and fixtures outside timing.
    for p in paths:
        p.read_bytes()
    order = ["BASELINE", "CANDIDATE"] if rep % 2 == 0 else ["CANDIDATE", "BASELINE"]
    arms = {name: run_arm(name, requests) for name in order}
    baseline = arms["BASELINE"]["outputs"]
    candidate = arms["CANDIDATE"]["outputs"]
    equal = [a["result"] == b["result"] for a, b in zip(baseline, candidate)]
    row = {
        "schema": "exact-crop-partial-recompute-case-v1",
        "workload": workload,
        "rep": rep,
        "pid": os.getpid(),
        "order": order,
        "requests": requests,
        "arms": arms,
        "result_equal": equal,
        "all_equal": all(equal),
        "fixture_sha256": {p.name: sha(p.read_bytes()) for p in paths},
        "source_sha256": {p.name: sha(p.read_bytes()) for p in [HERE/"candidate.py", HERE/"study.py", HERE/"audit.py", HERE/"PLAN.md", HERE/"ENVIRONMENT.json", HERE/"upstream"/"exact_crop_semantic_probe_v1.py", HERE/"upstream"/"inkscape_selection_frame_probe_v1.py"]},
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(row, sort_keys=True, indent=2) + "\n")
    return row


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workload", choices=WORKLOADS, required=True)
    ap.add_argument("--rep", type=int, choices=range(3), required=True)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    row = run_case(a.workload, a.rep, a.out)
    print(json.dumps({"workload": a.workload, "rep": a.rep, "all_equal": row["all_equal"], "out": str(a.out)}))


if __name__ == "__main__":
    main()
