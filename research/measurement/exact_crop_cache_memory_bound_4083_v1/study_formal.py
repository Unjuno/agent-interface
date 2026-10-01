"""Frozen-protocol runner with a separate reduced construction profile."""
from collections import OrderedDict
import argparse
import hashlib
import json
import platform
from pathlib import Path
import sys
import tempfile
import PIL

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "upstream"))
from candidate import DependencyCache
from exact_crop_semantic_probe_v1 import score_path
from inkscape_selection_frame_probe_v1 import load_exact_frame

FORMAL = {"width": 800, "height": 600, "count": 64, "capacity": 8,
          "box": [40, 30, 100, 90]}
CONSTRUCTION = {"width": 80, "height": 60, "count": 10, "capacity": 2,
               "box": [5, 4, 25, 20]}


def pixels_for(version, width, height):
    y, x = np.indices((height, width))
    return np.stack(((x * 7 + version * 19) % 256,
                     (y * 11 + version * 23) % 256,
                     (x + y * 3 + version * 31) % 256), axis=2).astype(np.uint8)


def sha_file(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class BoundedLRU(DependencyCache):
    def __init__(self, capacity):
        super().__init__()
        self.capacity = capacity
        self.order = OrderedDict()
        self.hits = []
        self.evicted = []

    def score(self, contract, image_path):
        artifact_sha = sha_file(Path(image_path))
        hit = artifact_sha in self.frames
        result = super().score(contract, image_path)
        self.hits.append(hit)
        self.order.pop(artifact_sha, None)
        self.order[artifact_sha] = None
        while len(self.order) > self.capacity:
            victim, _ = self.order.popitem(last=False)
            self.frames.pop(victim, None)
            for crop_key in list(self.crops):
                if crop_key[0] == victim:
                    del self.crops[crop_key]
            self.evicted.append(victim)
        return result


def pixel_bytes(cache):
    return sum(len(v[0].pixels) for v in cache.frames.values())


def execute(profile, output):
    width, height, count, capacity = (profile[k] for k in ("width", "height", "count", "capacity"))
    box = profile["box"]
    order = list(range(count)) + list(range(count - capacity, count))
    with tempfile.TemporaryDirectory(prefix="exact-crop-memory-run-") as td:
        root = Path(td)
        paths, contracts = [], []
        for version in range(count):
            path = root / f"frame-{version:03d}.png"
            Image.fromarray(pixels_for(version, width, height)).save(path, format="PNG", optimize=False)
            frame = load_exact_frame(path)
            array = np.frombuffer(frame.pixels, dtype=np.uint8).reshape(height, width, 3)
            expected = hashlib.sha256(array[box[1]:box[3], box[0]:box[2]].tobytes()).hexdigest()
            paths.append(path)
            contracts.append({"schema": "exact-rgb-crop-semantic-probe-v1",
                "probe_id": f"frame-{version:03d}", "box": box,
                "expected_crop_sha256": expected, "success_reason": "exact_crop_present",
                "grants_input_authority": False})

        unbounded, bounded, rows = DependencyCache(), BoundedLRU(capacity), []
        for request_i, version in enumerate(order):
            contract, path = contracts[version], paths[version]
            baseline = score_path(contract, path)
            unlimited = unbounded.score(contract, path)
            lru = bounded.score(contract, path)
            rows.append({"request_index": request_i, "version": version,
                "artifact_sha256": sha_file(path), "input_sha256": sha_file(path),
                "baseline": baseline, "unbounded": unlimited, "bounded": lru,
                "unbounded_pixel_bytes": pixel_bytes(unbounded),
                "bounded_pixel_bytes": pixel_bytes(bounded),
                "bounded_frame_hit_before": bounded.hits[-1],
                "bounded_frame_entries": list(bounded.order),
                "bounded_crop_artifacts": sorted({k[0] for k in bounded.crops})})

        source_files = [HERE / "study_formal.py", HERE / "audit_formal.py",
                        HERE / "upstream" / "candidate.py",
                        HERE / "upstream" / "exact_crop_semantic_probe_v1.py",
                        HERE / "upstream" / "inkscape_selection_frame_probe_v1.py"]
        source_hashes = {p.relative_to(HERE).as_posix(): sha_file(p) for p in source_files}
        raw = {"schema": "exact-crop-cache-memory-formal-raw-v1",
            "profile": "CONSTRUCTION_ONLY" if profile is CONSTRUCTION else "FORMAL",
            "environment": {"python": sys.version, "platform": platform.platform(),
                "numpy": np.__version__, "pillow": PIL.__version__},
            "source_sha256": source_hashes,
            "dimensions": [width, height], "capacity": capacity,
            "unique_versions": count, "request_order": order, "rows": rows,
            "unbounded_final_pixel_bytes": pixel_bytes(unbounded),
            "bounded_final_pixel_bytes": pixel_bytes(bounded),
            "bounded_final_frame_entries": list(bounded.order),
            "bounded_final_crop_artifacts": sorted({k[0] for k in bounded.crops}),
            "bounded_evicted_artifacts": bounded.evicted,
            "bounded_counters": bounded.counters}
        Path(output).write_text(json.dumps(raw, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("output")
    parser.add_argument("--construction", action="store_true")
    args = parser.parse_args()
    execute(CONSTRUCTION if args.construction else FORMAL, args.output)

