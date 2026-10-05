"""One-shot calibration on fresh seeds; held-out IDs are never read here."""
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent
P = json.loads((ROOT / "CALIBRATION_PROTOCOL.json").read_text())
PREDECESSOR = ROOT.parent / "image_jacobian_adaptation_7765_t0_20261005"
sys.path.insert(0, str(PREDECESSOR))
spec = importlib.util.spec_from_file_location("frozen_t0_runner", PREDECESSOR / "runner.py")
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


def main():
    rows = []
    for gain in P["fixed_gain_grid"]:
        runner.PROTOCOL["fixed_gain"] = gain
        for condition in P["conditions"]:
            for seed in range(P["training_seeds"][0], P["training_seeds"][1] + 1):
                rows.append({"gain": gain, **runner.trial(seed, condition, "fixed_gain")})
    eligible = []
    for gain in P["fixed_gain_grid"]:
        group = [r for r in rows if r["gain"] == gain]
        if all(r["goal_reached"] and not r["safety_violation"] for r in group):
            eligible.append((sum(r["candidate"]["corrections"] for r in group), gain))
    raw = "\n".join(json.dumps(r, sort_keys=True, separators=(",", ":")) for r in rows) + "\n"
    (ROOT / "CALIBRATION.jsonl").write_text(raw)
    result = {"rows": len(rows), "eligible": [g for _, g in sorted(eligible)],
              "selected_fixed_gain": min(eligible)[1] if eligible else None,
              "totals": [{"corrections": n, "gain": g} for n, g in sorted(eligible)],
              "sha256": hashlib.sha256(raw.encode()).hexdigest()}
    (ROOT / "CALIBRATION_RESULT.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result))
    if result["selected_fixed_gain"] is None: raise SystemExit(1)


if __name__ == "__main__": main()
