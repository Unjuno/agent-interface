"""One consumed synthetic allocation; no network, GUI or trained detector."""
import hashlib
import json
from pathlib import Path
import random
import sys
from policy import calibrate, predict

ROOT = Path(__file__).resolve().parent


def sample(seed, split, size, amplitude):
    rng = random.Random(seed * 10 + split)
    rows = []
    for _ in range(size):
        z = [3, 2, 1, 0]
        rng.shuffle(z)
        u = [rng.randrange(100) for _ in range(4)]
        s = [z[i] + (amplitude if u[i] < 3 else 0) for i in range(4)]
        rows.append({"u": u, "z": z, "s": s})
    return rows


def main():
    out = Path(sys.argv[1])
    config = json.loads((ROOT / "CONFIG.json").read_text())
    freeze = json.loads((ROOT / "FREEZE.json").read_text())
    raw = {"schema": 1, "allocation": config["allocation"],
           "config": config, "source": freeze["sha256"],
           "authority": False, "task_success": None, "blocks": []}
    for seed in config["seeds"]:
        cal = sample(seed, 0, 999, 10)
        residuals = [[abs(a-b) for a,b in zip(r["s"], r["z"])] for r in cal]
        radii = calibrate(residuals)
        block = {"seed": seed, "calibration": cal, "radii": radii, "profiles": []}
        for split, (name, amplitude) in enumerate(config["profiles"], 1):
            rows = sample(seed, split, 1000, amplitude)
            for row in rows:
                # Predictor receives no truth, profile, uniforms or expected winner.
                row["sets"] = predict(row["s"], radii)
            block["profiles"].append({"name": name, "rows": rows})
        raw["blocks"].append(block)
    data = json.dumps(raw, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    with (out / "RAW.json").open("xb") as f:
        f.write(data)
    print(json.dumps({"status":"COMPLETE", "calibration_rows":2997,
                      "evaluation_rows":6000, "raw_sha256":hashlib.sha256(data).hexdigest()}))

if __name__ == "__main__":
    main()
