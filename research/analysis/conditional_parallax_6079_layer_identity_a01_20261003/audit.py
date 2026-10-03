"""Independent raw-only auditor for #6838; does not import candidate.py."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from fractions import Fraction
from pathlib import Path

ALLOCATION = "CONDITIONAL-PARALLAX-6079-LAYER-IDENTITY-A01-20261003-01"
THRESHOLD_SQ = 25
MIN_SUPPORT = 2


def mean_delta(rows: list[dict], layer: str | None) -> tuple[Fraction, Fraction]:
    chosen = [r for r in rows if layer is None or r.get("layer") == layer]
    if not chosen:
        raise ValueError("empty layer")
    return (sum((Fraction(r["xy"][1][0] - r["xy"][0][0]) for r in chosen), Fraction()) / len(chosen),
            sum((Fraction(r["xy"][1][1] - r["xy"][0][1]) for r in chosen), Fraction()) / len(chosen))


def serialize(v: Fraction | None) -> dict | None:
    return None if v is None else {"n": v.numerator, "d": v.denominator}


def derive(case: dict) -> dict:
    tracks_by_scene = [scene.get("tracks", []) for scene in case.get("scenes", [])]
    diagnostic = None
    if len(tracks_by_scene) == 2:
        try:
            l, r = mean_delta(tracks_by_scene[0], None), mean_delta(tracks_by_scene[1], None)
            diagnostic = (l[0] - r[0]) ** 2 + (l[1] - r[1]) ** 2
        except (ValueError, KeyError, IndexError, TypeError, ZeroDivisionError):
            pass
    if not _contract(case, tracks_by_scene):
        return {"case_id": case.get("case_id"), "diagnostic_all_features_sq": serialize(diagnostic),
                "layer_relative_sq": None, "status": "UNKNOWN"}
    left, right = tracks_by_scene
    tl, tr = mean_delta(left, "target"), mean_delta(right, "target")
    bl, br = mean_delta(left, "background"), mean_delta(right, "background")
    dx = (tl[0] - bl[0]) - (tr[0] - br[0])
    dy = (tl[1] - bl[1]) - (tr[1] - br[1])
    value = dx * dx + dy * dy
    return {"case_id": case["case_id"], "diagnostic_all_features_sq": serialize(diagnostic),
            "layer_relative_sq": serialize(value),
            "status": "DISTINGUISHED" if value > THRESHOLD_SQ else "UNKNOWN"}


def _contract(case: dict, groups: list[list[dict]]) -> bool:
    probe = case.get("probe", {})
    if (probe.get("status") != "verified" or probe.get("source_id") != case.get("source_id")
            or probe.get("frame_ids") != case.get("frame_ids") or probe.get("intent_epoch") != "e1"):
        return False
    if len(groups) != 2 or [s.get("scene_id") for s in case["scenes"]] != ["left", "right"]:
        return False
    identities = []
    for group in groups:
        ids = [t.get("track_id") for t in group]
        if len(ids) != len(set(ids)):
            return False
        if any(t.get("membership") != "verified" or t.get("source_id") != case.get("source_id")
               or t.get("frame_ids") != case.get("frame_ids") for t in group):
            return False
        layer_ids = {layer: {t.get("track_id") for t in group if t.get("layer") == layer}
                     for layer in ("target", "background")}
        if any(len(layer_ids[x]) < MIN_SUPPORT for x in layer_ids):
            return False
        identities.append(layer_ids)
    return all(identities[0][layer] == identities[1][layer] for layer in ("target", "background"))


def check(public: dict, truth: dict, rows: list[dict], expected_public_sha: str) -> dict:
    public_bytes = (json.dumps(public, sort_keys=True, separators=(",", ":")) + "\n").encode()
    if hashlib.sha256(public_bytes).hexdigest() != expected_public_sha:
        raise ValueError("public fixture hash mismatch")
    cases = public.get("cases", [])
    expected_truth = truth.get("cases", {})
    if len(cases) != 8 or len(rows) != 8 or len(expected_truth) != 8:
        raise ValueError("expected exactly eight fixture/raw/truth rows")
    ids = [c.get("case_id") for c in cases]
    row_ids = [r.get("case_id") for r in rows]
    if len(set(ids)) != 8 or set(ids) != set(row_ids) or len(set(row_ids)) != 8:
        raise ValueError("case identity/count mismatch")
    by_id = {r["case_id"]: r for r in rows}
    for case in cases:
        cid = case["case_id"]
        want = derive(case)
        if by_id[cid] != want:
            raise ValueError(f"candidate/raw does not match independent reconstruction: {cid}")
        if want["status"] != expected_truth[cid]["expected"]:
            raise ValueError(f"fixture truth disagrees with independent reconstruction: {cid}")
        if want["status"] == "DISTINGUISHED" and want["layer_relative_sq"] is None:
            raise ValueError("distinction without a supported layer metric")
    by_case = {r["case_id"]: r for r in rows}
    if by_case["foreground-dominance-sham"]["diagnostic_all_features_sq"] != {"n": 784, "d": 1}:
        raise ValueError("foreground diagnostic did not preserve the planted all-feature failure")
    controls = corruption_controls(public, truth, rows, expected_public_sha)
    if len(controls) != 5 or not all(controls.values()):
        raise ValueError("one or more corruption controls were accepted")
    positives = [by_case[k] for k in ("target-parallax-positive-1", "target-parallax-positive-2")]
    if any(r["status"] != "DISTINGUISHED" for r in positives):
        raise ValueError("positive layer-relative controls not distinguished")
    if any(by_case[k]["status"] != "UNKNOWN" for k in (
            "foreground-dominance-sham", "zero-relative-motion", "ambiguous-layer-membership",
            "stale-track-identity", "invalid-probe-receipt", "insufficient-layer-support")):
        raise ValueError("negative/missing evidence did not stay UNKNOWN")
    return {"allocation": ALLOCATION, "status": "PASS_METHOD_SCOPED", "rows": 8,
            "positive_distinctions": 2, "unknown_controls": 6, "corruptions_rejected": 5,
            "foreground_all_feature_gap_sq": {"n": 784, "d": 1}, "errors": []}


def corruption_controls(public: dict, truth: dict, rows: list[dict], expected_sha: str) -> dict[str, bool]:
    checks: dict[str, bool] = {}
    mutated = copy.deepcopy(public)
    mutated["cases"][2]["scenes"][1]["tracks"][0]["layer"] = "target"
    checks["layer_relabel_public"] = _raises(mutated, truth, rows, expected_sha,
                                               "candidate/raw does not match independent reconstruction")
    mutated = copy.deepcopy(public)
    mutated["cases"][0]["probe"]["status"] = "unknown"
    checks["probe_status_public"] = _raises(mutated, truth, rows, expected_sha,
                                              "candidate/raw does not match independent reconstruction")
    mutated = copy.deepcopy(public)
    mutated["cases"][0]["scenes"][1]["tracks"][0]["frame_ids"] = ["f0", "other-frame"]
    checks["frame_binding_public"] = _raises(mutated, truth, rows, expected_sha,
                                               "candidate/raw does not match independent reconstruction")
    checks["dropped_raw_row"] = _raises(public, truth, rows[:-1], expected_sha,
                                          "expected exactly eight fixture/raw/truth rows")
    mutated_rows = copy.deepcopy(rows)
    mutated_rows[2]["status"] = "DISTINGUISHED"
    checks["forged_raw_classification"] = _raises(public, truth, mutated_rows, expected_sha,
                                                    "candidate/raw does not match independent reconstruction")
    return checks


def _raises(public: dict, truth: dict, rows: list[dict], expected_sha: str,
            reason: str) -> bool:
    try:
        check(public, truth, rows, expected_sha)
    except ValueError as error:
        return str(error) == reason
    except (KeyError, TypeError, IndexError):
        return False
    return False


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--truth", type=Path, required=True)
    parser.add_argument("--raw", type=Path, required=True)
    parser.add_argument("--expected-public-sha256", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    input_bytes = args.input.read_bytes()
    public = json.loads(input_bytes)
    truth = json.loads(args.truth.read_bytes())
    raw_bytes = args.raw.read_bytes()
    rows = [json.loads(line) for line in raw_bytes.splitlines()]
    result = check(public, truth, rows, args.expected_public_sha256)
    result.update({"public_sha256": hashlib.sha256(input_bytes).hexdigest(),
                   "truth_sha256": hashlib.sha256(args.truth.read_bytes()).hexdigest(),
                   "raw_sha256": hashlib.sha256(raw_bytes).hexdigest(),
                   "raw_bytes": len(raw_bytes), "mutation_controls": corruption_controls(
                       public, truth, rows, args.expected_public_sha256)})
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(result, stream, sort_keys=True, separators=(",", ":"))
        stream.write("\n")
    print(f"status={result['status']} rows={result['rows']} errors=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
