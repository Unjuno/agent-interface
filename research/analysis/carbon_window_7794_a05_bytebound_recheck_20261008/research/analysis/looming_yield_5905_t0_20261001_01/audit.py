import base64
import hashlib
import json
import math
import sys


def audit(fixture, raw):
    errors = []
    frame_map = {}
    for row in raw.get("frames", []):
        frame_map.setdefault(row.get("case"), []).append(row)
        try:
            image = base64.b64decode(row["bytes_b64"], validate=True)
            if hashlib.sha256(image).hexdigest() != row.get("sha256"):
                errors.append("frame_digest:" + str(row.get("case")))
            header, pixels = image.split(b"\n255\n", 1)
            if header != f"P5\n{cfg_width(fixture)} {cfg_width(fixture)}".encode() or len(pixels) != cfg_width(fixture)**2:
                errors.append("frame_shape:" + str(row.get("case")))
        except Exception:
            errors.append("frame_encoding:" + str(row.get("case")))
    cfg = fixture["render"]
    outcomes = {r.get("id"): r for r in raw.get("cases", [])}
    expected_ids = {c["id"] for c in fixture["cases"]}
    if set(outcomes) != expected_ids:
        errors.append("case_set")
    eligible = []
    unknown = []
    for case in fixture["cases"]:
        result = outcomes.get(case["id"], {})
        rows = sorted(frame_map.get(case["id"], []), key=lambda x: x.get("index", -1))
        if case["kind"] == "control":
            if result.get("status") != "UNKNOWN" or result.get("safe") is not False or result.get("release_requested") is not False:
                errors.append("control_not_unknown:" + case["id"])
            if result.get("reason") != case["violation"]:
                errors.append("control_reason:" + case["id"])
            if case["violation"] == "track_identity_changed" and len({r.get("track") for r in rows}) < 2:
                errors.append("track_swap_not_in_raw:" + case["id"])
            if case["violation"] == "timestamps_not_increasing" and all(b > a for a,b in zip([r.get("t") for r in rows],[r.get("t") for r in rows][1:])):
                errors.append("timestamp_corruption_not_in_raw:" + case["id"])
            unknown.append(case["id"])
            continue
        count = int(math.ceil((case["z0"] / case["speed"]) / cfg["dt"]))
        expected_times = [round(i * cfg["dt"], 10) for i in range(count)]
        ts = [r.get("t") for r in rows]
        if len(rows) != len(expected_times) or ts != expected_times:
            errors.append("frame_schedule:" + case["id"])
            continue
        decision = result.get("decision")
        if result.get("status") != "CUE" or not decision or result.get("release_requested") is not True:
            errors.append("missed_cue:" + case["id"])
            continue
        i = decision.get("frame_index", -1)
        if not isinstance(i, int) or i <= 0 or i >= len(expected_times):
            errors.append("decision_index:" + case["id"])
            continue
        t0, t1 = expected_times[i-1], expected_times[i]
        z0 = case["z0"] - case["speed"]*t0
        z1 = case["z0"] - case["speed"]*t1
        r0 = math.sqrt(sum(base64.b64decode(rows[i-1]["bytes_b64"], validate=True).split(b"\n255\n",1)[1])/255.0/math.pi)
        r1 = math.sqrt(sum(base64.b64decode(rows[i]["bytes_b64"], validate=True).split(b"\n255\n",1)[1])/255.0/math.pi)
        recomputed = r1 / ((r1-r0)/(t1-t0))
        truth = z1/case["speed"]
        release_lead = truth - cfg["release_latency_s"]
        if not math.isclose(decision.get("estimate_s", math.nan), recomputed, rel_tol=1e-10, abs_tol=1e-10):
            errors.append("estimate_mismatch:" + case["id"])
        if not math.isclose(decision.get("truth_s", math.nan), truth, rel_tol=1e-10, abs_tol=1e-10):
            errors.append("truth_mismatch:" + case["id"])
        if abs(recomputed-truth) > 0.20:
            errors.append("estimate_error_gate:" + case["id"])
        if not math.isclose(decision.get("release_at_s", math.nan), t1+cfg["release_latency_s"], rel_tol=1e-10, abs_tol=1e-10):
            errors.append("release_clock_mismatch:" + case["id"])
        if not math.isclose(decision.get("contact_at_s", math.nan), case["z0"]/case["speed"], rel_tol=1e-10, abs_tol=1e-10):
            errors.append("contact_clock_mismatch:" + case["id"])
        if recomputed > cfg["threshold_ttc_s"] or release_lead <= 0:
            errors.append("late_release:" + case["id"])
        eligible.append({"id":case["id"],"estimate_error_s":abs(recomputed-truth),"release_lead_s":release_lead})
    # Ensure raw rows are bound to the declared source and one track for eligible cases.
    for case in fixture["cases"]:
        if case["kind"] == "approach":
            rows = sorted(frame_map.get(case["id"], []), key=lambda x:x.get("index", -1))
            if any(r.get("source") != "session-1" or r.get("track") != "track-1" for r in rows):
                errors.append("identity_binding:" + case["id"])
            for row in rows:
                try:
                    pixels = base64.b64decode(row["bytes_b64"], validate=True).split(b"\n255\n",1)[1]
                    measured = math.sqrt(sum(pixels)/255.0/math.pi)
                    t = row["t"]
                    expected = fixture["render"]["K"]/(case["z0"]-case["speed"]*t)
                    if expected < fixture["render"]["radius_max"] and abs(measured-expected) > 0.75:
                        errors.append("render_geometry:" + case["id"])
                        break
                except Exception:
                    errors.append("render_decode:" + case["id"])
                    break
    return {"result":"PASS_METHOD_SCOPED" if not errors else "FAIL_METHOD","errors":errors,"eligible":eligible,"unknown_controls":unknown,"counts":{"cases":len(outcomes),"frames":len(raw.get("frames",[])),"eligible":len(eligible),"unknown_controls":len(unknown)}}


def cfg_width(fixture):
    return fixture["render"]["width"]


if __name__ == "__main__":
    with open(sys.argv[1], encoding="utf-8") as f:
        fixture = json.load(f)
    with open(sys.argv[2], encoding="utf-8") as f:
        raw = json.load(f)
    result = audit(fixture, raw)
    with open(sys.argv[3], "w", encoding="utf-8") as f:
        json.dump(result, f, sort_keys=True, indent=2)
        f.write("\n")
    print(json.dumps(result, sort_keys=True))
