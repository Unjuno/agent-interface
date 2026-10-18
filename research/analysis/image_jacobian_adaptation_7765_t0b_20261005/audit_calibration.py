"""Independent reconstruction of the separate-seed calibration table."""
import hashlib
import json
import math
import random
from pathlib import Path

ROOT = Path(__file__).parent
P = json.loads((ROOT / "CALIBRATION_PROTOCOL.json").read_text())


def plant(seed, condition):
    rng = random.Random(seed * 117 + len(condition) * 7919)
    if condition == "gain_drift":
        return [[rng.uniform(0.58, 1.52), 0.0], [0.0, rng.uniform(0.58, 1.52)]]
    a, b = rng.uniform(0.72, 1.28), rng.uniform(0.72, 1.28)
    if condition == "cross_coupling":
        c, d = rng.uniform(-0.38, 0.38), rng.uniform(-0.38, 0.38)
    else:
        c, d = rng.uniform(-0.30, 0.30), rng.uniform(-0.30, 0.30)
    return [[a, c], [d, b]]


def audit(rows):
    errors = []
    gains = P["fixed_gain_grid"]
    keys = [(r.get("gain"), r.get("condition"), r.get("seed")) for r in rows]
    expected = {(g, c, s) for g in gains for c in P["conditions"] for s in range(1000, 1020)}
    if set(keys) != expected or len(keys) != len(expected):
        errors.append("CALIBRATION_GRID_INCOMPLETE_OR_DUPLICATE")
    totals = {g: 0 for g in gains}
    eligible = {g: True for g in gains}
    for row in rows:
        g, c, s = row["gain"], row["condition"], row["seed"]
        mat = plant(s, c)
        state = [0.0, 0.0]
        for i, u in enumerate(row["actions"]):
            delta = [sum(mat[k][j] * u[j] for j in range(2)) for k in range(2)]
            state = [state[k] + delta[k] for k in range(2)]
            err = [row["start_error"][k] - state[k] for k in range(2)]
            try:
                event = row["candidate"]["rows"][i]
                if event["action"] != u or event["after"] != err:
                    errors.append(f"EVENT_MISMATCH:{g}:{c}:{s}:{i}")
            except (IndexError, KeyError):
                errors.append(f"EVENT_MISSING:{g}:{c}:{s}:{i}")
            if math.hypot(*u) > 12.0 + 1e-9:
                errors.append(f"ACTION_BOUND:{g}:{c}:{s}:{i}")
        terminal = math.hypot(row["start_error"][0] - state[0], row["start_error"][1] - state[1])
        if abs(terminal - row["terminal_error"]) > 1e-9:
            errors.append(f"TERMINAL_MISMATCH:{g}:{c}:{s}")
        totals[g] += row["candidate"]["corrections"]
        if not row["goal_reached"] or row["safety_violation"] or terminal > 1.0:
            eligible[g] = False
    qualified = sorted((totals[g], g) for g in gains if eligible[g])
    selected = qualified[0][1] if qualified else None
    return {"errors": errors, "rows": len(rows), "totals": totals,
            "eligible": eligible, "selected_fixed_gain": selected,
            "qualified_order": [{"corrections": x, "gain": g} for x, g in qualified]}


def main():
    path = ROOT / "CALIBRATION.jsonl"
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    result = audit(rows)
    result["raw_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    (ROOT / "CALIBRATION_AUDIT.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    if result["errors"] or result["selected_fixed_gain"] is None:
        raise SystemExit(1)


if __name__ == "__main__": main()
