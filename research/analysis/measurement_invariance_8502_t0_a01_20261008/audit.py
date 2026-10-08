"""Independent raw-only audit for Issue #8502 T0 A01; does not import candidate.py."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any


EXPECTED_PARAMETERS = {"min_n_per_group": 100, "threshold_margin": 0.15, "association_margin": 0.22}


class AuditFailure(Exception):
    pass


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def independent_summary(rows: list[list[int]], item_count: int) -> tuple[list[float], dict[str, float]]:
    n = len(rows)
    cdf = []
    for col in range(item_count):
        biggest = 0.0
        for boundary in (0, 1, 2, 3):
            count = 0
            for row in rows:
                if row[col] <= boundary:
                    count += 1
            biggest = max(biggest, count / n)
        cdf.append(biggest)
    assoc: dict[str, float] = {}
    for left in range(item_count):
        for right in range(left + 1, item_count):
            sx = sum(row[left] for row in rows)
            sy = sum(row[right] for row in rows)
            sxx = sum(row[left] * row[left] for row in rows)
            syy = sum(row[right] * row[right] for row in rows)
            sxy = sum(row[left] * row[right] for row in rows)
            vx = sxx - sx * sx / n
            vy = syy - sy * sy / n
            cov = sxy - sx * sy / n
            assoc[f"{left}-{right}"] = 0.0 if vx <= 0.0 or vy <= 0.0 else cov / (vx * vy) ** 0.5
    return cdf, assoc


def independently_classify(fixture: dict[str, Any], item_count: int) -> dict[str, Any]:
    ga, gb = fixture["groups"]["A"], fixture["groups"]["B"]
    if len(ga) < EXPECTED_PARAMETERS["min_n_per_group"] or len(gb) < EXPECTED_PARAMETERS["min_n_per_group"]:
        return {"classification": "UNCERTAIN", "reason": "UNDERPOWERED_N", "threshold_items": [], "loading_items": [], "association_edges": []}
    ta, tb = independent_summary(ga, item_count)[0], independent_summary(gb, item_count)[0]
    changed_thresholds = [index for index, (x, y) in enumerate(zip(ta, tb)) if abs(x - y) > EXPECTED_PARAMETERS["threshold_margin"]]
    if changed_thresholds:
        return {"classification": "THRESHOLD_NONINVARIANCE", "reason": "CUMULATIVE_CATEGORY_DIFFERENCE", "threshold_items": changed_thresholds, "loading_items": [], "association_edges": []}
    aa, ab = independent_summary(ga, item_count)[1], independent_summary(gb, item_count)[1]
    edges = sorted(key for key in aa if abs(aa[key] - ab[key]) > EXPECTED_PARAMETERS["association_margin"])
    if not edges:
        return {"classification": "COMPATIBLE_SCREEN", "reason": "NO_GROSS_MOMENT_DIFFERENCE", "threshold_items": [], "loading_items": [], "association_edges": []}
    common = set(map(int, edges[0].split("-")))
    for edge in edges[1:]:
        common.intersection_update(map(int, edge.split("-")))
    if len(edges) >= 3 and len(common) == 1:
        return {"classification": "LOADING_PATTERN_NONINVARIANCE", "reason": "SINGLE_ITEM_STAR", "threshold_items": [], "loading_items": sorted(common), "association_edges": edges}
    return {"classification": "STRUCTURE_NONINVARIANCE", "reason": "NON_STAR_ASSOCIATION_PATTERN", "threshold_items": [], "loading_items": [], "association_edges": edges}


def validate(fixtures_bytes: bytes, truth_bytes: bytes, candidate_bytes: bytes, freeze: dict, root: Path) -> list[str]:
    errors: list[str] = []
    if sha(fixtures_bytes) != freeze.get("inputs", {}).get("fixtures.json"):
        errors.append("fixture_digest_mismatch")
    if sha(truth_bytes) != freeze.get("inputs", {}).get("truth.json"):
        errors.append("truth_digest_mismatch")
    for name, digest in freeze.get("sources", {}).items():
        if not (root / name).is_file() or sha((root / name).read_bytes()) != digest:
            errors.append(f"source_digest_mismatch:{name}")
    try:
        fixtures, truth, candidate = json.loads(fixtures_bytes), json.loads(truth_bytes), json.loads(candidate_bytes)
    except Exception as exc:
        return errors + [f"json_invalid:{type(exc).__name__}"]
    if candidate.get("schema") != "issue8502-t0-a01-candidate-v1":
        errors.append("candidate_schema_mismatch")
    if candidate.get("fixture_sha256") != sha(fixtures_bytes):
        errors.append("candidate_input_binding_mismatch")
    if candidate.get("parameters") != EXPECTED_PARAMETERS:
        errors.append("candidate_gate_drift")
    cases = {entry["fixture_id"]: entry for entry in fixtures.get("fixtures", [])}
    results = {entry.get("fixture_id"): entry for entry in candidate.get("results", [])}
    truth_cases = truth.get("cases", {})
    if len(cases) != 5 or len(results) != len(cases) or set(cases) != set(results) or set(cases) != set(truth_cases):
        errors.append("fixture_or_result_set_mismatch")
    for fixture_id, fixture in cases.items():
        groups = fixture.get("groups", {})
        if set(groups) != {"A", "B"} or not groups["A"] or not groups["B"]:
            errors.append(f"group_shape:{fixture_id}")
            continue
        for group, rows in groups.items():
            if any(len(row) != fixtures.get("item_count") or any(type(value) is not int or not 0 <= value <= 4 for value in row) for row in rows):
                errors.append(f"response_domain:{fixture_id}:{group}")
        expected = truth_cases.get(fixture_id, {})
        actual = results.get(fixture_id, {})
        reconstructed = independently_classify(fixture, fixtures["item_count"])
        if actual.get("classification") != expected.get("expected") or actual.get("classification") != reconstructed["classification"]:
            errors.append(f"classification_mismatch:{fixture_id}")
        for field in ("reason", "threshold_items", "loading_items", "association_edges"):
            if actual.get(field, [] if field != "reason" else None) != reconstructed[field]:
                errors.append(f"independent_{field}_mismatch:{fixture_id}")
        localization = expected.get("localization", [])
        if actual.get("threshold_items", []) != (localization if expected.get("expected") == "THRESHOLD_NONINVARIANCE" else []):
            errors.append(f"threshold_localization_mismatch:{fixture_id}")
        if actual.get("loading_items", []) != (localization if expected.get("expected") == "LOADING_PATTERN_NONINVARIANCE" else []):
            errors.append(f"loading_localization_mismatch:{fixture_id}")
    return errors


def main() -> None:
    root = Path(__file__).resolve().parent
    fixture_bytes = (root / "fixtures.json").read_bytes()
    truth_bytes = (root / "truth.json").read_bytes()
    candidate_bytes = (root / "candidate.json").read_bytes()
    freeze = json.loads((root / "FREEZE.json").read_bytes())
    errors = validate(fixture_bytes, truth_bytes, candidate_bytes, freeze, root)
    mutations = {}
    baseline_candidate = json.loads(candidate_bytes)
    for mutation in ("flip_invariant_label", "drop_result", "alter_localization", "change_candidate_parameter"):
        altered = copy.deepcopy(baseline_candidate)
        if mutation == "flip_invariant_label":
            altered["results"][0]["classification"] = "THRESHOLD_NONINVARIANCE"
        elif mutation == "drop_result":
            altered["results"].pop()
        elif mutation == "alter_localization":
            altered["results"][1]["threshold_items"] = [1]
        else:
            altered["parameters"]["min_n_per_group"] = 10
        bad = validate(fixture_bytes, truth_bytes, json.dumps(altered, sort_keys=True, separators=(",", ":")).encode(), freeze, root)
        mutations[mutation] = bool(bad)
    altered_fixture = bytearray(fixture_bytes)
    altered_fixture[-2] = ord(" ") if altered_fixture[-2] != ord(" ") else ord("\n")
    mutations["tampered_fixture_bytes"] = bool(validate(bytes(altered_fixture), truth_bytes, candidate_bytes, freeze, root))
    result = {
        "schema": "issue8502-t0-a01-independent-audit-v1",
        "decision": "METHOD_PASS_SCOPED" if not errors and all(mutations.values()) else "FAIL_METHOD",
        "fixture_count": 5,
        "independent_errors": errors,
        "mutation_rejections": mutations,
        "scope": "synthetic ordinal screening method only; no human-data comparability claim",
        "input_sha256": {"fixtures.json": sha(fixture_bytes), "truth.json": sha(truth_bytes), "candidate.json": sha(candidate_bytes)},
    }
    payload = (json.dumps(result, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n").encode("utf-8")
    with (root / "AUDIT.json").open("xb") as stream:
        stream.write(payload)
    print(json.dumps({"decision": result["decision"], "errors": errors, "mutation_rejections": mutations, "sha256": sha(payload)}, sort_keys=True))


if __name__ == "__main__":
    main()
