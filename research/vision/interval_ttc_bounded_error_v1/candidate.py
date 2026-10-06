"""Candidate: emit point and set-valued TTC estimates from public rows only."""
import json
import math
import sys


def estimate(history):
    if any(not math.isfinite(x["t_s"]) for x in history) or any(
            history[i]["t_s"] >= history[i + 1]["t_s"] for i in range(len(history) - 1)):
        return None, None
    if any(history[i].get("radius_px") is None and history[i + 1].get("radius_px") is None
           for i in range(len(history) - 1)):
        return None, None
    seen = [x for x in history if x.get("radius_px") is not None]
    if len(seen) < 2 or any(not math.isfinite(x["t_s"]) or not math.isfinite(x["radius_px"])
                            or not math.isfinite(x["bound_px"]) or x["bound_px"] < 0
                            for x in seen):
        return None, None
    if len({x["track_id"] for x in seen}) != 1:
        return None, None
    if any(seen[i]["t_s"] >= seen[i + 1]["t_s"] for i in range(len(seen) - 1)):
        return None, None
    slopes = []
    for a, b in zip(seen, seen[1:]):
        dt = b["t_s"] - a["t_s"]
        lo_a, hi_a = a["radius_px"] - a["bound_px"], a["radius_px"] + a["bound_px"]
        lo_b, hi_b = b["radius_px"] - b["bound_px"], b["radius_px"] + b["bound_px"]
        if lo_a <= 0 or lo_b <= 0:
            return None, None
        slopes.append(((lo_b - hi_a) / dt, (hi_b - lo_a) / dt))
    v_lo = max(x[0] for x in slopes)
    v_hi = min(x[1] for x in slopes)
    if v_lo <= 0 or v_hi < v_lo:
        return None, None
    last = seen[-1]
    lo, hi = last["radius_px"] - last["bound_px"], last["radius_px"] + last["bound_px"]
    if lo <= 0:
        return None, None
    point = None
    a, b = seen[-2:]
    dv = b["radius_px"] - a["radius_px"]
    if dv > 0:
        point = b["radius_px"] * (b["t_s"] - a["t_s"]) / dv
    return point, (lo / v_hi, hi / v_lo)


def run(source, destination):
    output = []
    with open(source, encoding="utf-8") as f:
        for line in f:
            row = json.loads(line)
            estimates = []
            history = []
            for observation in row["history"]:
                history.append(observation)
                point, interval = estimate(history)
                valid = [x for x in history if x.get("radius_px") is not None]
                pixel = area = None
                if len(valid) >= 2 and valid[-2]["radius_px"] > 0 and valid[-1]["radius_px"] > 0:
                    r0, r1 = valid[-2]["radius_px"], valid[-1]["radius_px"]
                    pixel, area = abs(r1-r0), abs((r1*r1)/(r0*r0)-1.0)
                estimates.append({"t_s": observation["t_s"], "point_ttc_s": point,
                                  "interval_s": list(interval) if interval else None,
                                  "pixel_change_px": pixel, "relative_area_change": area})
            output.append({"id": row["id"], "estimates": estimates})
    with open(destination, "w", encoding="utf-8") as f:
        for row in output:
            f.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")


if __name__ == "__main__":
    run(sys.argv[1], sys.argv[2])
