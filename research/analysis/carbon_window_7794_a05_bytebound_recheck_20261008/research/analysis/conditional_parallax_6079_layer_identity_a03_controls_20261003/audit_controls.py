"""Independent A03 reconstruction and corruption-control audit for #6843."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from fractions import Fraction
from pathlib import Path

ALLOCATION = "CONDITIONAL-PARALLAX-6079-LAYER-IDENTITY-A03-20261003-01"


def avg(tracks, layer=None):
    selected = [x for x in tracks if layer is None or x.get("layer") == layer]
    if not selected:
        raise ValueError("empty layer")
    return tuple(sum((Fraction(t["xy"][1][axis] - t["xy"][0][axis]) for t in selected), Fraction())
                 / len(selected) for axis in (0, 1))


def valid(case):
    source, frames = case.get("source_id"), case.get("frame_ids")
    probe = case.get("probe", {})
    if any((probe.get("status") != "verified", probe.get("source_id") != source,
            probe.get("frame_ids") != frames, probe.get("intent_epoch") != "e1")):
        return False
    scenes = case.get("scenes", [])
    if len(scenes) != 2 or [s.get("scene_id") for s in scenes] != ["left", "right"]:
        return False
    identity_maps = []
    for scene in scenes:
        tracks = scene.get("tracks", [])
        ids = [t.get("track_id") for t in tracks]
        if len(ids) != len(set(ids)):
            return False
        if any(t.get("membership") != "verified" or t.get("source_id") != source
               or t.get("frame_ids") != frames for t in tracks):
            return False
        layers = {name: {t["track_id"] for t in tracks if t.get("layer") == name}
                  for name in ("target", "background")}
        if min(map(len, layers.values())) < 2:
            return False
        identity_maps.append(layers)
    return all(identity_maps[0][k] == identity_maps[1][k]
               for k in ("target", "background"))


def expected(case):
    scenes = case.get("scenes", [])
    all_gap = None
    if len(scenes) == 2:
        try:
            l, r = avg(scenes[0].get("tracks", [])), avg(scenes[1].get("tracks", []))
            all_gap = (l[0] - r[0]) ** 2 + (l[1] - r[1]) ** 2
        except (ValueError, KeyError, IndexError, TypeError):
            pass
    serial = lambda x: None if x is None else {"n": x.numerator, "d": x.denominator}
    cid = case.get("case_id")
    if not valid(case):
        return {"case_id": cid, "diagnostic_all_features_sq": serial(all_gap),
                "layer_relative_sq": None, "status": "UNKNOWN"}
    left, right = (s["tracks"] for s in scenes)
    tl, tr, bl, br = avg(left, "target"), avg(right, "target"), avg(left, "background"), avg(right, "background")
    dx, dy = (tl[0] - bl[0]) - (tr[0] - br[0]), (tl[1] - bl[1]) - (tr[1] - br[1])
    rel = dx * dx + dy * dy
    return {"case_id": cid, "diagnostic_all_features_sq": serial(all_gap),
            "layer_relative_sq": serial(rel), "status": "DISTINGUISHED" if rel > 25 else "UNKNOWN"}


def public_digest(public):
    canonical = (json.dumps(public, sort_keys=True, separators=(",", ":")) + "\n").encode()
    return hashlib.sha256(canonical).hexdigest()


def baseline(public, truth, rows, expected_sha):
    if public_digest(public) != expected_sha:
        raise ValueError("public_hash_mismatch")
    cases, labels = public.get("cases", []), truth.get("cases", {})
    ids = [c.get("case_id") for c in cases]
    row_ids = [r.get("case_id") for r in rows]
    if len(cases) != 8 or len(rows) != 8 or len(labels) != 8:
        raise ValueError("exact_row_count_mismatch")
    if len(set(ids)) != 8 or set(ids) != set(row_ids) or len(set(row_ids)) != 8:
        raise ValueError("case_identity_mismatch")
    by_id = {r["case_id"]: r for r in rows}
    wanted = {c["case_id"]: expected(c) for c in cases}
    for cid, row in wanted.items():
        if by_id[cid] != row:
            raise ValueError("independent_reconstruction_mismatch")
        if labels[cid].get("expected") != row["status"]:
            raise ValueError("truth_reconciliation_mismatch")
    foreground = by_id["foreground-dominance-sham"]
    if foreground["diagnostic_all_features_sq"] != {"n": 784, "d": 1}:
        raise ValueError("foreground_diagnostic_mismatch")
    if foreground["layer_relative_sq"] != {"n": 0, "d": 1}:
        raise ValueError("foreground_relative_mismatch")
    return wanted


def must_reject(public, truth, rows, sha, reason):
    try:
        baseline(public, truth, rows, sha)
    except ValueError as exc:
        return str(exc) == reason
    return False


def control_results(public, truth, rows, sha):
    controls = {}
    changed = copy.deepcopy(public)
    old = changed["cases"][2]["scenes"][1]["tracks"][4]["layer"]
    changed["cases"][2]["scenes"][1]["tracks"][4]["layer"] = "target"
    controls["actual_foreground_relabel"] = old == "foreground" and must_reject(
        changed, truth, rows, sha, "public_hash_mismatch")
    changed = copy.deepcopy(public)
    changed["cases"][0]["probe"]["status"] = "unknown"
    controls["probe_status"] = must_reject(changed, truth, rows, sha, "public_hash_mismatch")
    changed = copy.deepcopy(public)
    changed["cases"][0]["scenes"][1]["tracks"][0]["frame_ids"] = ["f0", "alien"]
    controls["frame_binding"] = must_reject(changed, truth, rows, sha, "public_hash_mismatch")
    controls["dropped_row"] = must_reject(public, truth, rows[:-1], sha, "exact_row_count_mismatch")
    forged = copy.deepcopy(rows)
    forged[2]["status"] = "DISTINGUISHED"
    controls["forged_classification"] = must_reject(
        public, truth, forged, sha, "independent_reconstruction_mismatch")
    return controls


def run(public, truth, rows, sha):
    wanted = baseline(public, truth, rows, sha)
    controls = control_results(public, truth, rows, sha)
    if len(controls) != 5 or not all(controls.values()):
        raise ValueError("mutation_control_failure")
    if sum(r["status"] == "DISTINGUISHED" for r in wanted.values()) != 2:
        raise ValueError("positive_count_mismatch")
    return {"allocation": ALLOCATION, "status": "PASS_AUDIT_CONTROLS_RECONCILED",
            "rows": 8, "positive_distinctions": 2, "unknown_controls": 6,
            "corruptions_rejected": 5, "mutation_controls": controls,
            "foreground_all_feature_gap_sq": {"n": 784, "d": 1}}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--input", type=Path, required=True)
    p.add_argument("--truth", type=Path, required=True)
    p.add_argument("--raw", type=Path, required=True)
    p.add_argument("--expected-public-sha256", required=True)
    p.add_argument("--out", type=Path, required=True)
    a = p.parse_args()
    pb, tb, rb = a.input.read_bytes(), a.truth.read_bytes(), a.raw.read_bytes()
    result = run(json.loads(pb), json.loads(tb), [json.loads(x) for x in rb.splitlines()], a.expected_public_sha256)
    result.update({"public_sha256": hashlib.sha256(pb).hexdigest(),
                   "truth_sha256": hashlib.sha256(tb).hexdigest(),
                   "raw_sha256": hashlib.sha256(rb).hexdigest(),
                   "auditor_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()})
    a.out.parent.mkdir(parents=True, exist_ok=True)
    with a.out.open("x", encoding="utf-8", newline="\n") as f:
        json.dump(result, f, sort_keys=True, separators=(",", ":"))
        f.write("\n")
    print("status=PASS_AUDIT_CONTROLS_RECONCILED rows=8 corruptions=5")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
