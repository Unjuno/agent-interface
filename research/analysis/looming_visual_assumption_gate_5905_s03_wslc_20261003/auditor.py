"""Independent raw-only image/decision reconstruction; never imports candidate.py."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
import tempfile


def decode_frame(path):
    raw = Path(path).read_bytes()
    header, pixels = raw.split(b"\n", 3)[:3], raw.split(b"\n", 3)[3]
    if header != [b"P5", b"96 96", b"255"] or len(pixels) != 9216:
        raise ValueError("malformed PGM")
    return raw, pixels


def _cc_centers(values):
    todo = set(values)
    centers = []
    while todo:
        start = todo.pop()
        stack = [start]
        group = [start]
        while stack:
            k = stack.pop()
            x, y = k % 96, k // 96
            neighbors = []
            if x: neighbors.append(k - 1)
            if x < 95: neighbors.append(k + 1)
            if y: neighbors.append(k - 96)
            if y < 95: neighbors.append(k + 96)
            for n in neighbors:
                if n in todo:
                    todo.remove(n)
                    stack.append(n)
                    group.append(n)
        centers.append((sum(k % 96 for k in group) / len(group),
                        sum(k // 96 for k in group) / len(group)))
    return sorted(centers, key=lambda p: (p[1] >= 48, p[0] >= 48))


def _measure(pixels):
    pts = [(i % 96, i // 96) for i, v in enumerate(pixels) if v >= 170]
    if not pts:
        raise ValueError("missing visible target")
    cx = sum(p[0] for p in pts) / len(pts)
    cy = sum(p[1] for p in pts) / len(pts)
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    width, height = max(xs) - min(xs) + 1, max(ys) - min(ys) + 1
    buckets = [0, 0, 0, 0]
    for x, y in pts:
        buckets[(2 if y >= 48 else 0) + (1 if x >= 48 else 0)] += 1
    return {"xy": (cx, cy), "r": math.sqrt(len(pts) / math.pi),
            "aspect": max(width, height) / min(width, height),
            "q": [x / len(pts) for x in buckets],
            "tone": sum(pixels[i] for i, _ in enumerate(pixels) if pixels[i] >= 170) / len(pts),
            "anchors": _cc_centers([i for i, v in enumerate(pixels) if v == 128]),
            "flow": sorted(math.hypot(i % 96 - cx, i // 96 - cy)
                           for i, v in enumerate(pixels) if v == 80)}


def _median(a):
    a = sorted(a)
    if len(a) % 2:
        return a[len(a) // 2]
    return (a[len(a) // 2 - 1] + a[len(a) // 2]) / 2


def _derive(m0, m1, dt):
    aa, ab = m0["anchors"], m1["anchors"]
    if len(aa) < 4 or len(ab) < 4:
        return "UNKNOWN", "missing_anchors", None, None, None
    if len(aa) != 4 or len(ab) != 4:
        return "UNKNOWN", "unstable_anchors", None, None, None
    delta = [math.dist(x, y) for x, y in zip(aa, ab)]
    if min(delta) > 2:
        scales = [math.dist(y, (48, 48)) / math.dist(x, (48, 48)) for x, y in zip(aa, ab)]
        if max(scales) - min(scales) < .12 and min(scales) > 1.04:
            return "REJECT", "common_mode_zoom", max(delta), None, None
    if max(delta) > 4:
        return "UNKNOWN", "unstable_anchors", max(delta), None, None
    imbalance = max(max(m0["q"]) - min(m0["q"]), max(m1["q"]) - min(m1["q"]))
    aspect_change = max(m0["aspect"], m1["aspect"]) / min(m0["aspect"], m1["aspect"])
    if imbalance > .18 and aspect_change > 1.35:
        return "REJECT", "partial_occlusion", max(delta), None, None
    if math.dist(m0["xy"], m1["xy"]) > 3:
        return "REJECT", "off_axis_motion", max(delta), None, None
    if imbalance > .18:
        return "REJECT", "partial_occlusion", max(delta), None, None
    if aspect_change > 1.35:
        return "REJECT", "shape_deformation", max(delta), None, None
    if abs(m1["tone"] - m0["tone"]) > 12:
        return "REJECT", "appearance_discontinuity", max(delta), None, None
    if len(m0["flow"]) < 20 or len(m1["flow"]) < 20:
        return "UNKNOWN", "insufficient_scene_flow", max(delta), None, None
    flow_scale = _median([b / a for a, b in zip(m0["flow"], m1["flow"]) if a > 0])
    if flow_scale < 1.05:
        return "UNKNOWN", "insufficient_scene_flow", max(delta), flow_scale, None
    if flow_scale > 1.5:
        return "UNKNOWN", "unstable_scene_flow", max(delta), flow_scale, None
    if m1["r"] <= m0["r"]:
        return "REJECT", "no_target_expansion", max(delta), flow_scale, None
    ttc = dt * m0["r"] / (m1["r"] - m0["r"])
    if ttc <= 0 or ttc > 1000:
        return "UNKNOWN", "ttc_outside_frozen_window", max(delta), flow_scale, ttc
    return "CUE", "coherent_centered_expansion", max(delta), flow_scale, ttc


def audit(fixture_path, oracle_path, raw_path, check_corruptions=True):
    root = Path(fixture_path).resolve().parent
    fixture = json.loads(Path(fixture_path).read_text(encoding="utf-8"))
    oracle = json.loads(Path(oracle_path).read_text(encoding="utf-8"))
    raw = [json.loads(line) for line in Path(raw_path).read_text(encoding="utf-8").splitlines() if line]
    truth = {x["case_id"]: x for x in oracle["cases"]}
    case_map = {x["case_id"]: x for x in fixture["cases"]}
    errors = []
    if len(raw) != len(case_map) or {x.get("case_id") for x in raw} != set(case_map):
        errors.append("row cardinality or IDs mismatch")
    raw_map = {x.get("case_id"): x for x in raw}
    for cid, case in case_map.items():
        if cid not in raw_map:
            continue
        row, expected = raw_map[cid], truth[cid]
        try:
            b0, p0 = decode_frame(root / case["frame0"])
            b1, p1 = decode_frame(root / case["frame1"])
            hashes = [hashlib.sha256(b0).hexdigest(), hashlib.sha256(b1).hexdigest()]
            if hashes != expected["frame_sha256"] or row.get("frame_sha256") != hashes:
                errors.append(f"frame provenance mismatch: {cid}")
            if row.get("source_epoch") != case["source_epoch"]:
                errors.append(f"epoch mismatch: {cid}")
            m0, m1 = _measure(p0), _measure(p1)
            decision, reason, anchor_motion, flow_scale, ttc = _derive(m0, m1, case["t1_ms"] - case["t0_ms"])
            if (decision, reason) != (expected["expected"], expected["reason"]):
                errors.append(f"oracle/independent reconstruction mismatch: {cid}")
            if (row.get("classification"), row.get("reason")) != (decision, reason):
                errors.append(f"candidate disposition mismatch: {cid}")
            geometry = row.get("geometry", {})
            numeric_metrics = {
                "radius0": m0["r"], "radius1": m1["r"],
                "aspect0": m0["aspect"], "aspect1": m1["aspect"]}
            for key, value in numeric_metrics.items():
                if not math.isclose(geometry.get(key, float("nan")), value, rel_tol=1e-9, abs_tol=1e-9):
                    errors.append(f"geometry metric mismatch {key}: {cid}")
            for key, value in (("center0", m0["xy"]), ("center1", m1["xy"])):
                got = geometry.get(key)
                if not isinstance(got, list) or len(got) != 2 or any(
                        not math.isclose(got[j], value[j], rel_tol=1e-9, abs_tol=1e-9) for j in range(2)):
                    errors.append(f"geometry metric mismatch {key}: {cid}")
            got_anchor, got_flow = geometry.get("anchor_motion_max"), geometry.get("scene_flow_ratio")
            if ((anchor_motion is None) != (got_anchor is None) or
                    (anchor_motion is not None and not math.isclose(got_anchor, anchor_motion, rel_tol=1e-9, abs_tol=1e-9))):
                errors.append(f"anchor metric mismatch: {cid}")
            if ((flow_scale is None) != (got_flow is None) or
                    (flow_scale is not None and not math.isclose(got_flow, flow_scale, rel_tol=1e-9, abs_tol=1e-9))):
                errors.append(f"scene flow metric mismatch: {cid}")
            want_cue = decision == "CUE"
            if row.get("release_request") is not want_cue:
                errors.append(f"release decision mismatch: {cid}")
            if want_cue:
                relerr = abs(row.get("ttc_ms", 0) - ttc) / ttc
                lead = row.get("release_lead_ms")
                if relerr > oracle["positive_ttc_error_fraction_max"]:
                    errors.append(f"TTC error exceeds bound: {cid}")
                if expected.get("ttc_ms") is None or abs(expected["ttc_ms"] - ttc) / ttc > oracle["positive_ttc_error_fraction_max"]:
                    errors.append(f"oracle TTC disagrees with image reconstruction: {cid}")
                if lead is None or not (oracle["release_lead_ms_min"] <= lead <= oracle["release_lead_ms_max"]):
                    errors.append(f"release lead outside bound: {cid}")
                if abs(lead - row.get("ttc_ms", 0)) > 1e-6:
                    errors.append(f"release lead not tied to TTC: {cid}")
            elif row.get("ttc_ms") is not None or row.get("release_lead_ms") is not None:
                errors.append(f"non-cue contains TTC/release lead: {cid}")
        except Exception as ex:
            errors.append(f"reconstruction error {cid}: {ex}")

    pair = oracle["frame_identical_pair"]
    if all(cid in case_map for cid in pair):
        ca, cb = (case_map[cid] for cid in pair)
        images_a = [(root / ca[k]).read_bytes() for k in ("frame0", "frame1")]
        images_b = [(root / cb[k]).read_bytes() for k in ("frame0", "frame1")]
        if images_a != images_b:
            errors.append("non-identifiable pair pixels differ")
        if all(cid in raw_map for cid in pair):
            ra, rb = (raw_map[cid] for cid in pair)
            xa, xb = dict(ra), dict(rb)
            xa.pop("case_id", None); xb.pop("case_id", None)
            if xa != xb:
                errors.append("pixel-identical pair decisions/metrics differ")

    corruption_results = {}
    if check_corruptions:
        def reject(name, mutation):
            changed = copy.deepcopy(raw)
            mutation(changed)
            with tempfile.TemporaryDirectory() as tmp:
                changed_path = Path(tmp) / "mutated.jsonl"
                changed_path.write_text("".join(json.dumps(x, sort_keys=True, separators=(",", ":")) + "\n" for x in changed), encoding="utf-8")
                verdict = audit(fixture_path, oracle_path, changed_path, check_corruptions=False)["verdict"]
            corruption_results[name] = verdict != "PASS_METHOD_SCOPED"
        reject("missing_row", lambda x: x.pop())
        reject("duplicate_row", lambda x: x.append(copy.deepcopy(x[0])))
        reject("forged_frame_hash", lambda x: x[0]["frame_sha256"].__setitem__(0, "0" * 64))
        reject("forged_geometry", lambda x: x[0]["geometry"].__setitem__("radius1", 999.0))
        reject("false_safe_control", lambda x: _setrow(x, "k04", "CUE", True, 500.0))
        reject("fabricated_release_lead", lambda x: _setrow(x, "k01", "CUE", True, 9999.0))
    if check_corruptions and not all(corruption_results.values()):
        errors.append("a frozen corruption was not rejected")
    gates = {"all_12_rows_reconstructed": len(raw) == 12 and not any("mismatch" in e for e in errors),
             "all_three_eligible_cases_cued": sum(x.get("classification") == "CUE" for x in raw) == 3,
             "all_controls_fail_closed": all(x.get("classification") != "CUE" for x in raw if truth.get(x.get("case_id"), {}).get("expected") != "CUE"),
             "pixel_identical_pair_same_unknown": all(case_map[c]["case_id"] in raw_map and raw_map[c]["classification"] == "UNKNOWN" for c in pair) and (len(pair) == 2 and all((root / case_map[pair[0]][k]).read_bytes() == (root / case_map[pair[1]][k]).read_bytes() for k in ("frame0", "frame1"))),
             "all_six_corruptions_rejected": (not check_corruptions) or all(corruption_results.values())}
    return {"verdict": "PASS_METHOD_SCOPED" if not errors and all(gates.values()) else "FAIL_AUDIT",
            "n_rows": len(raw), "errors": errors, "gates": gates,
            "corruption_rejected": corruption_results}


def _setrow(rows, cid, classification, release, lead):
    r = next(x for x in rows if x["case_id"] == cid)
    r["classification"], r["release_request"] = classification, release
    r["release_lead_ms"] = lead
    r["ttc_ms"] = lead


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--fixture", required=True)
    ap.add_argument("--oracle", required=True)
    ap.add_argument("--raw", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    result = audit(args.fixture, args.oracle, args.raw)
    Path(args.out).write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"verdict": result["verdict"], "n_rows": result["n_rows"],
                      "errors": result["errors"], "corruption_rejected": result["corruption_rejected"]}, sort_keys=True))
    raise SystemExit(0 if result["verdict"] == "PASS_METHOD_SCOPED" else 1)
