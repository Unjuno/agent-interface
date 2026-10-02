"""Construction-only bounded cache retention probe; no GUI or input authority."""
from collections import OrderedDict
import hashlib
import json
from pathlib import Path
import sys
import tempfile

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from candidate import DependencyCache
from upstream.exact_crop_semantic_probe_v1 import score_path
from upstream.inkscape_selection_frame_probe_v1 import load_exact_frame

WIDTH, HEIGHT = 80, 60
BOX = [5, 4, 25, 20]
COUNT, CAPACITY = 10, 2


def fixture_pixels(version):
    y, x = np.indices((HEIGHT, WIDTH))
    return np.stack(((x * 7 + version * 19) % 256,
                     (y * 11 + version * 23) % 256,
                     (x + y * 3 + version * 31) % 256), axis=2).astype(np.uint8)


def file_sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class BoundedLRU(DependencyCache):
    def __init__(self, capacity):
        super().__init__()
        self.capacity = capacity
        self.order = OrderedDict()
        self.evicted = []
        self.frame_hit_before = []

    def score(self, contract, image_path):
        artifact_sha = file_sha(Path(image_path))
        hit = artifact_sha in self.frames
        result = super().score(contract, image_path)
        self.frame_hit_before.append(hit)
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


def resident_pixel_bytes(cache):
    return sum(len(value[0].pixels) for value in cache.frames.values())


def main(output_path):
    with tempfile.TemporaryDirectory(prefix="exact-crop-lru-construction-") as td:
        root = Path(td)
        paths, contracts = [], []
        for version in range(COUNT):
            path = root / f"frame-{version:02d}.png"
            Image.fromarray(fixture_pixels(version)).save(path, format="PNG", optimize=False)
            frame = load_exact_frame(path)
            pixels = np.frombuffer(frame.pixels, dtype=np.uint8).reshape(HEIGHT, WIDTH, 3)
            expected = hashlib.sha256(pixels[BOX[1]:BOX[3], BOX[0]:BOX[2]].tobytes()).hexdigest()
            paths.append(path)
            contracts.append({"schema": "exact-rgb-crop-semantic-probe-v1",
                "probe_id": f"construction-{version:02d}", "box": BOX,
                "expected_crop_sha256": expected, "success_reason": "exact_crop_present",
                "grants_input_authority": False})

        order = list(range(COUNT)) + [COUNT - 2, COUNT - 1]
        unbounded, bounded = DependencyCache(), BoundedLRU(CAPACITY)
        rows = []
        for index in order:
            contract, path = contracts[index], paths[index]
            baseline = score_path(contract, path)
            all_cache = unbounded.score(contract, path)
            lru = bounded.score(contract, path)
            rows.append({"version": index, "artifact_sha256": file_sha(path),
                "input_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "baseline": baseline, "unbounded": all_cache, "bounded": lru,
                "unbounded_pixel_bytes": resident_pixel_bytes(unbounded),
                "bounded_pixel_bytes": resident_pixel_bytes(bounded),
                "bounded_frame_hit_before": bounded.frame_hit_before[-1],
                "bounded_frame_entries": list(bounded.order),
                "bounded_crop_entries": sorted({key[0] for key in bounded.crops})})

        result = {"schema": "exact-crop-cache-memory-construction-v1",
            "formal": False, "dimensions": [WIDTH, HEIGHT], "capacity": CAPACITY,
            "unique_versions": COUNT, "request_order": order, "rows": rows,
            "unbounded_final_pixel_bytes": resident_pixel_bytes(unbounded),
            "bounded_final_pixel_bytes": resident_pixel_bytes(bounded),
            "bounded_final_frame_entries": list(bounded.order),
            "bounded_final_crop_artifacts": sorted({key[0] for key in bounded.crops}),
            "bounded_evicted_artifacts": bounded.evicted,
            "bounded_counters": bounded.counters}
        Path(output_path).write_text(json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: study.py OUTPUT.json")
    main(sys.argv[1])

