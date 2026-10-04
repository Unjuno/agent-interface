"""Separate-seed fixed-gain calibration; does not inspect held-out outcomes."""
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).parent
SPEC = json.loads((ROOT / "CALIBRATION_PROTOCOL.json").read_text())
PREDECESSOR = ROOT.parent / "image_jacobian_adaptation_7765_t0_20261005"
spec = importlib.util.spec_from_file_location("t0_runner", PREDECESSOR / "runner.py")
runner = importlib.util.module_from_spec(spec)
import sys
sys.path.insert(0, str(PREDECESSOR))
spec.loader.exec_module(runner)


def main():
    records = []
    for gain in SPEC["fixed_gain_grid"]:
        runner.PROTOCOL["fixed_gain"] = gain
        for condition in SPEC["conditions"]:
            for seed in range(1000, 1020):
                records.append({"gain": gain, **runner.trial(seed, condition, "fixed_gain")})
    eligible = []
    for gain in SPEC["fixed_gain_grid"]:
        group = [r for r in records if r["gain"] == gain]
        if all(r["goal_reached"] and not r["safety_violation"] for r in group):
            eligible.append((sum(r["candidate"]["corrections"] for r in group), gain))
    selected = min(eligible)[1] if eligible else None
    raw = "\n".join(json.dumps(r, sort_keys=True, separators=(",", ":")) for r in records) + "\n"
    (ROOT / "CALIBRATION.jsonl").write_text(raw)
    result = {"rows": len(records), "selected_fixed_gain": selected,
              "eligible_totals": [{"corrections": n, "gain": g} for n, g in sorted(eligible)],
              "sha256": hashlib.sha256(raw.encode()).hexdigest(), "eligible_all": bool(eligible)}
    (ROOT / "CALIBRATION_RESULT.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result))
    if selected is None:
        raise SystemExit(1)


if __name__ == "__main__": main()
