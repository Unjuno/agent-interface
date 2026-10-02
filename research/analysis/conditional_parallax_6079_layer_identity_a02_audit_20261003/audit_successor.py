"""Independent, non-recursive raw-only audit for successor allocation A02."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from fractions import Fraction
from pathlib import Path

ALLOCATION = "CONDITIONAL-PARALLAX-6079-LAYER-IDENTITY-A02-20261003-01"
EXPECTED = {
    "target-parallax-positive-1": "DISTINGUISHED",
    "target-parallax-positive-2": "DISTINGUISHED",
    "foreground-dominance-sham": "UNKNOWN",
    "zero-relative-motion": "UNKNOWN",
    "ambiguous-layer-membership": "UNKNOWN",
    "stale-track-identity": "UNKNOWN",
    "invalid-probe-receipt": "UNKNOWN",
    "insufficient-layer-support": "UNKNOWN",
}


def mean(tracks: list[dict], layer: str | None) -> tuple[Fraction, Fraction]:
    chosen = [t for t in tracks if layer is None or t.get("layer") == layer]
    if not chosen:
        raise ValueError("empty selection")
    return tuple(sum((Fraction(t["xy"][1][i] - t["xy"][0][i]) for t in chosen), Fraction())
                 / len(chosen) for i in (0, 1))  # type: ignore[return-value]


def contract(case: dict) -> bool:
    source, frames = case.get("source_id"), case.get("frame_ids")
    probe = case.get("probe", {})
    if (probe.get("status"), probe.get("source_id"), probe.get("frame_ids"),
            probe.get("intent_epoch")) != ("verified", source, frames, "e1"):
        return False
    scenes = case.get("scenes", [])
    if len(scenes) != 2 or [s.get("scene_id") for s in scenes] != ["left", "right"]:
        return False
    identities = []
    for scene in scenes:
        tracks = scene.get("tracks", [])
        ids = [t.get("track_id") for t in tracks]
        if len(ids) != len(set(ids)):
            return False
        if any(t.get("membership") != "verified" or t.get("source_id") != source
               or t.get("frame_ids") != frames for t in tracks):
            return False
        sets = {name: {t["track_id"] for t in tracks if t.get("layer") == name}
                for name in ("target", "background")}
        if any(len(sets[name]) < 2 for name in sets):
            return False
        identities.append(sets)
    return all(identities[0][name] == identities[1][name]
               for name in ("target", "background"))


def expected_row(case: dict) -> dict:
    scenes = case.get("scenes", [])
    diagnostic = None
    if len(scenes) == 2:
        try:
            left, right = mean(scenes[0].get("tracks", []), None), mean(scenes[1].get("tracks", []), None)
            diagnostic = (left[0] - right[0]) ** 2 + (left[1] - right[1]) ** 2
        except (ValueError, KeyError, IndexError, TypeError):
            pass
    def serial(v):
        return None if v is None else {"n": v.numerator, "d": v.denominator}
    cid = case.get("case_id")
    if not contract(case):
        return {"case_id": cid, "diagnostic_all_features_sq": serial(diagnostic),
                "layer_relative_sq": None, "status": "UNKNOWN"}
    left, right = (s["tracks"] for s in scenes)
    tl, tr = mean(left, "target"), mean(right, "target")
    bl, br = mean(left, "background"), mean(right, "background")
    dx, dy = (tl[0] - bl[0]) - (tr[0] - br[0]), (tl[1] - bl[1]) - (tr[1] - br[1])
    value = dx * dx + dy * dy
    return {"case_id": cid, "diagnostic_all_features_sq": serial(diagnostic),
            "layer_relative_sq": serial(value),
            "status": "DISTINGUISHED" if value > 25 else "UNKNOWN"}


def reconcile(public: dict, truth: dict, raw: list[dict], public_sha: str) -> dict:
    canonical = (json.dumps(public, sort_keys=True, separators=(",", ":")) + "\n").encode()
    if hashlib.sha256(canonical).hexdigest() != public_sha:
        raise ValueError("public_hash_mismatch")
    cases, labels = public.get("cases", []), truth.get("cases", {})
    ids = [case.get("case_id") for case in cases]
    raw_ids = [row.get("case_id") for row in raw]
    if len(cases) != 8 or len(raw) != 8 or len(labels) != 8:
        raise ValueError("exact_row_count_mismatch")
    if len(set(ids)) != 8 or set(ids) != set(raw_ids) or len(set(raw_ids)) != 8:
        raise ValueError("case_id_set_mismatch")
    by_id = {row["case_id"]: row for row in raw}
    reconstructed = {case["case_id"]: expected_row(case) for case in cases}
    for cid, want in reconstructed.items():
        if by_id[cid] != want:
            raise ValueError("independent_raw_reconstruction_mismatch")
        if labels[cid].get("expected") != want["status"]:
            raise ValueError("truth_reconciliation_mismatch")
    if by_id["foreground-dominance-sham"]["diagnostic_all_features_sq"] != {"n": 784, "d": 1}:
        raise ValueError("foreground_sham_control_mismatch")
    return {"rows": 8, "reconstructed": reconstructed}


def require_reason(public: dict, truth: dict, raw: list[dict], sha: str, reason: str) -> bool:
    try:
        reconcile(public, truth, raw, sha)
    except ValueError as error:
        return str(error) == reason
    return False


def mutations(public: dict, truth: dict, raw: list[dict], sha: str) -> dict[str, bool]:
    altered = copy.deepcopy(public)
    altered["cases"][2]["scenes"][1]["tracks"][0]["layer"] = "target"
    layer = require_reason(altered, truth, raw, sha, "public_hash_mismatch")
    altered = copy.deepcopy(public)
    altered["cases"][0]["probe"]["status"] = "unknown"
    probe = require_reason(altered, truth, raw, sha, "public_hash_mismatch")
    altered = copy.deepcopy(public)
    altered["cases"][0]["scenes"][1]["tracks"][0]["frame_ids"] = ["f0", "other-frame"]
    frames = require_reason(altered, truth, raw, sha, "public_hash_mismatch")
    dropped = require_reason(public, truth, raw[:-1], sha, "exact_row_count_mismatch")
    forged = copy.deepcopy(raw)
    forged[2]["status"] = "DISTINGUISHED"
    classification = require_reason(public, truth, forged, sha,
                                    "independent_raw_reconstruction_mismatch")
    return {"public_layer_relabel_hash_rejected": layer,
            "public_probe_status_hash_rejected": probe,
            "public_frame_binding_hash_rejected": frames,
            "dropped_raw_count_rejected": dropped,
            "forged_raw_classification_rejected": classification}


def run(public: dict, truth: dict, raw: list[dict], public_sha: str) -> dict:
    result = reconcile(public, truth, raw, public_sha)
    controls = mutations(public, truth, raw, public_sha)
    if len(controls) != 5 or not all(controls.values()):
        raise ValueError("mutation_control_failure")
    rows = result["reconstructed"]
    if [rows[k]["status"] for k in EXPECTED] != list(EXPECTED.values()):
        raise ValueError("declared_class_criteria_failure")
    return {"allocation": ALLOCATION, "status": "PASS_AUDIT_RECONCILED",
            "rows": 8, "positive_distinctions": 2, "unknown_controls": 6,
            "corruptions_rejected": 5, "mutation_controls": controls,
            "foreground_all_feature_gap_sq": {"n": 784, "d": 1}}


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--input", type=Path, required=True)
    p.add_argument("--truth", type=Path, required=True)
    p.add_argument("--raw", type=Path, required=True)
    p.add_argument("--expected-public-sha256", required=True)
    p.add_argument("--out", type=Path, required=True)
    a = p.parse_args()
    public_bytes, truth_bytes, raw_bytes = a.input.read_bytes(), a.truth.read_bytes(), a.raw.read_bytes()
    public, truth = json.loads(public_bytes), json.loads(truth_bytes)
    raw = [json.loads(line) for line in raw_bytes.splitlines()]
    result = run(public, truth, raw, a.expected_public_sha256)
    result.update({"public_sha256": hashlib.sha256(public_bytes).hexdigest(),
                   "truth_sha256": hashlib.sha256(truth_bytes).hexdigest(),
                   "raw_sha256": hashlib.sha256(raw_bytes).hexdigest(),
                   "auditor_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()})
    a.out.parent.mkdir(parents=True, exist_ok=True)
    with a.out.open("x", encoding="utf-8", newline="\n") as f:
        json.dump(result, f, sort_keys=True, separators=(",", ":"))
        f.write("\n")
    print(f"status={result['status']} rows=8 corruptions=5")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
