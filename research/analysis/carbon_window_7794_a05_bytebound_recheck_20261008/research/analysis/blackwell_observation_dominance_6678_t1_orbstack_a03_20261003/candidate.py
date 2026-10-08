import json
import sys
from collections import Counter
from fractions import Fraction
from itertools import product
from pathlib import Path

from png_decode import region_label

sys.path.insert(0, str(Path(__file__).parent))
from dependency_t0_candidate import find_garbling


def frac(pair):
    return Fraction(pair[0], pair[1])


def main(raw_dir, out_path):
    root = Path(__file__).parent
    states = json.loads((root / "states.json").read_text())
    schedule = json.loads((root / "schedule.json").read_text())
    manifest = json.loads((Path(raw_dir) / "manifest.json").read_text())
    allowed = states["allowed_pixel_rgb"]
    channels = {name: {s["id"]: Counter() for s in states["states"]} for name in states["channels"]}
    for row in schedule["captures"]:
        capture = next(c for c in manifest["captures"] if c["capture_id"] == row["capture_id"])
        base = Path(raw_dir) / row["capture_id"]
        full = (base / "full_png.png").read_bytes()
        left = (base / "left_roi_png.png").read_bytes()
        right = (base / "right_roi_png.png").read_bytes()
        full_label = "|".join(region_label(full, box, allowed) for box in states["pixel_regions"]["full_png"])
        left_label = region_label(left, states["pixel_regions"]["left_roi_png"][0], allowed)
        right_label = region_label(right, states["pixel_regions"]["right_roi_png"][0], allowed)
        channels["full_png"][row["state"]][full_label] += 1
        channels["left_roi_png"][row["state"]][left_label] += 1
        channels["right_roi_png"][row["state"]][right_label] += 1
        ax = (base / "accessibility_snapshot.txt").read_text()
        expected_state = next(s for s in states["states"] if s["id"] == row["state"])
        channels["accessibility_snapshot"][row["state"]]["exact:" + str(row["state"]) if expected_state["left"] in ax and expected_state["right"] in ax else "unknown"] += 1
        delta = (base / "mutation_delta.json").read_text()
        channels["mutation_delta"][row["state"]]["changed" if json.loads(delta) else "quiet"] += 1
    kernels = {}
    for channel, by_state in channels.items():
        outcomes = sorted({o for counts in by_state.values() for o in counts})
        kernels[channel] = {
            "outputs": outcomes,
            "counts_by_state": {s: [by_state[s][o] for o in outcomes] for s in sorted(by_state)},
            "kernel": [[ [by_state[s][o], states["captures_per_state"]] for o in outcomes] for s in sorted(by_state)],
        }
    relations = {}
    for left, left_data in kernels.items():
        for right, right_data in kernels.items():
            source = [[Fraction(n, d) for n, d in row] for row in left_data["kernel"]]
            target = [[Fraction(n, d) for n, d in row] for row in right_data["kernel"]]
            cert = find_garbling(source, target)
            relations[f"{left}>={right}"] = None if cert is None else [[[v.numerator, v.denominator] for v in row] for row in cert]
    prior = [frac(x) for x in states["prior"]]
    risks = {}
    for problem, spec in states["decision_problems"].items():
        risks[problem] = {}
        for name, data in kernels.items():
            kernel = [[Fraction(n, d) for n, d in row] for row in data["kernel"]]
            best = None
            for rule in product(range(len(spec["loss"][0])), repeat=len(kernel[0])):
                val = sum(prior[s] * kernel[s][o] * spec["loss"][s][rule[o]]
                          for s in range(len(kernel)) for o in range(len(kernel[s])))
                best = val if best is None or val < best else best
            risks[problem][name] = [best.numerator, best.denominator]
    result = {"schema": "blackwell-6678-t1-candidate-v1", "browser_version": manifest["browser_version"], "channels": kernels, "relations": relations, "risks": risks}
    Path(out_path).write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: candidate.py RAW_DIR OUT_JSON")
    main(sys.argv[1], sys.argv[2])
