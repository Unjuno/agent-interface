"""A02 raw-only independent audit of immutable Issue #8502 T0 A01 artifacts."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


PARAMETERS = {"min_n_per_group": 100, "threshold_margin": 0.15, "association_margin": 0.22}
TRUTH = {
    "F01": ("COMPATIBLE_SCREEN", [], []),
    "F02": ("THRESHOLD_NONINVARIANCE", [2], []),
    "F03": ("LOADING_PATTERN_NONINVARIANCE", [], [2]),
    "F04": ("STRUCTURE_NONINVARIANCE", [], []),
    "F05": ("UNCERTAIN", [], []),
}
EXPECTED_A01_ERRORS = ["classification_mismatch:F02", "independent_reason_mismatch:F02", "independent_threshold_items_mismatch:F02"]


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def parse(data: bytes) -> Any:
    return json.loads(data.decode("utf-8"))


def group_profile(rows: list[list[int]], items: int) -> tuple[list[list[float]], dict[str, float]]:
    """Compute every cumulative category proportion and Pearson item association."""
    n = len(rows)
    cdfs: list[list[float]] = []
    for col in range(items):
        category_counts = [0, 0, 0, 0, 0]
        for response in rows:
            category_counts[response[col]] += 1
        running = 0
        cumulative = []
        for count in category_counts[:4]:
            running += count
            cumulative.append(running / n)
        cdfs.append(cumulative)

    sums = [sum(response[col] for response in rows) for col in range(items)]
    squares = [sum(response[col] * response[col] for response in rows) for col in range(items)]
    associations: dict[str, float] = {}
    for left in range(items):
        for right in range(left + 1, items):
            cross = sum(response[left] * response[right] for response in rows)
            cov_n = n * cross - sums[left] * sums[right]
            var_left_n = n * squares[left] - sums[left] * sums[left]
            var_right_n = n * squares[right] - sums[right] * sums[right]
            value = 0.0 if var_left_n <= 0 or var_right_n <= 0 else cov_n / (var_left_n * var_right_n) ** 0.5
            associations[f"{left}-{right}"] = value
    return cdfs, associations


def decision(fixture: dict[str, Any], item_count: int) -> dict[str, Any]:
    a, b = fixture["groups"]["A"], fixture["groups"]["B"]
    if min(len(a), len(b)) < PARAMETERS["min_n_per_group"]:
        return {"classification": "UNCERTAIN", "threshold_items": [], "loading_items": [], "association_edges": []}
    cdf_a, corr_a = group_profile(a, item_count)
    cdf_b, corr_b = group_profile(b, item_count)
    threshold_items = []
    for item in range(item_count):
        if max(abs(x - y) for x, y in zip(cdf_a[item], cdf_b[item])) > PARAMETERS["threshold_margin"]:
            threshold_items.append(item)
    if threshold_items:
        return {"classification": "THRESHOLD_NONINVARIANCE", "threshold_items": threshold_items, "loading_items": [], "association_edges": []}
    edges = sorted(edge for edge in corr_a if abs(corr_a[edge] - corr_b[edge]) > PARAMETERS["association_margin"])
    if not edges:
        return {"classification": "COMPATIBLE_SCREEN", "threshold_items": [], "loading_items": [], "association_edges": []}
    common = set(map(int, edges[0].split("-")))
    for edge in edges[1:]:
        common.intersection_update(map(int, edge.split("-")))
    if len(edges) >= 3 and len(common) == 1:
        return {"classification": "LOADING_PATTERN_NONINVARIANCE", "threshold_items": [], "loading_items": sorted(common), "association_edges": edges}
    return {"classification": "STRUCTURE_NONINVARIANCE", "threshold_items": [], "loading_items": [], "association_edges": edges}


def semantic_errors(fixtures: dict, candidate: dict) -> list[str]:
    errors = []
    fixture_rows = {row["fixture_id"]: row for row in fixtures.get("fixtures", [])}
    candidate_rows = {row.get("fixture_id"): row for row in candidate.get("results", [])}
    if len(fixture_rows) != 5 or len(candidate_rows) != len(fixture_rows) or set(fixture_rows) != set(candidate_rows) or set(fixture_rows) != set(TRUTH):
        errors.append("fixture_result_id_set")
    if candidate.get("parameters") != PARAMETERS:
        errors.append("parameters")
    for name, fixture in fixture_rows.items():
        actual = candidate_rows.get(name, {})
        independently = decision(fixture, fixtures.get("item_count", 0))
        expected_class, expected_thresholds, expected_loadings = TRUTH[name]
        if actual.get("classification") != expected_class or actual.get("classification") != independently["classification"]:
            errors.append(f"class:{name}")
        if actual.get("threshold_items", []) != expected_thresholds or actual.get("threshold_items", []) != independently["threshold_items"]:
            errors.append(f"threshold_localization:{name}")
        if actual.get("loading_items", []) != expected_loadings or actual.get("loading_items", []) != independently["loading_items"]:
            errors.append(f"loading_localization:{name}")
        if actual.get("association_edges", []) != independently["association_edges"]:
            errors.append(f"association_edges:{name}")
        if name == "F05" and actual.get("classification") != "UNCERTAIN":
            errors.append("sparse_not_uncertain")
    return errors


def verify_bundle(a01: Path, freeze: dict) -> tuple[list[str], dict[str, bytes]]:
    errors: list[str] = []
    blobs: dict[str, bytes] = {}
    for name, expected in freeze.get("a01_files", {}).items():
        path = a01 / name
        if not path.is_file():
            errors.append(f"missing_a01_file:{name}")
            continue
        raw = path.read_bytes()
        blobs[name] = raw
        if digest(raw) != expected:
            errors.append(f"a01_file_digest:{name}")
    for name, expected in freeze.get("a01_sources", {}).items():
        path = a01 / name
        if not path.is_file() or digest(path.read_bytes()) != expected:
            errors.append(f"a01_source_digest:{name}")
    try:
        a01_freeze = parse(blobs["FREEZE.json"])
        a01_audit = parse(blobs["AUDIT.json"])
        if a01_freeze.get("issue") != 8502 or a01_freeze.get("main_sha") != freeze.get("main_sha"):
            errors.append("a01_freeze_identity")
        if a01_audit.get("decision") != "FAIL_METHOD" or a01_audit.get("independent_errors") != EXPECTED_A01_ERRORS:
            errors.append("a01_failure_not_preserved")
        if not all(a01_audit.get("mutation_rejections", {}).values()):
            errors.append("a01_mutation_controls_not_preserved")
        fixtures, truth, candidate = (parse(blobs[name]) for name in ("fixtures.json", "truth.json", "candidate.json"))
        expected_truth = {key: {"expected": value[0], "localization": value[1] or value[2]} for key, value in TRUTH.items()}
        if truth.get("cases") != expected_truth:
            errors.append("a01_truth_table_mismatch")
        if candidate.get("schema") != "issue8502-t0-a01-candidate-v1" or candidate.get("fixture_sha256") != digest(blobs["fixtures.json"]):
            errors.append("a01_candidate_input_binding")
        if candidate.get("parameters") != PARAMETERS:
            errors.append("a01_candidate_gate_drift")
        errors.extend(semantic_errors(fixtures, candidate))
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        errors.append(f"a01_payload_invalid:{type(exc).__name__}")
    return errors, blobs


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--a01-dir", required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    a01 = Path(args.a01_dir).resolve()
    freeze_raw = (root / "FREEZE.json").read_bytes()
    freeze = parse(freeze_raw)
    errors = []
    for name, expected in freeze.get("a02_sources", {}).items():
        if not (root / name).is_file() or digest((root / name).read_bytes()) != expected:
            errors.append(f"a02_source_digest:{name}")
    bundle_errors, blobs = verify_bundle(a01, freeze)
    errors.extend(bundle_errors)
    fixtures = parse(blobs["fixtures.json"]) if "fixtures.json" in blobs else {}
    candidate = parse(blobs["candidate.json"]) if "candidate.json" in blobs else {}
    mutations = {}
    for name in ("wrong_class", "missing_result", "wrong_threshold_item", "sparse_as_invariant", "malformed_edge"):
        mutated = json.loads(json.dumps(candidate))
        if name == "wrong_class":
            mutated["results"][0]["classification"] = "THRESHOLD_NONINVARIANCE"
        elif name == "missing_result":
            mutated["results"].pop()
        elif name == "wrong_threshold_item":
            mutated["results"][1]["threshold_items"] = [1]
        elif name == "sparse_as_invariant":
            mutated["results"][4]["classification"] = "COMPATIBLE_SCREEN"
        else:
            mutated["results"][3]["association_edges"] = ["0-1"]
        mutations[name] = bool(semantic_errors(fixtures, mutated))
    changed_bytes = bytearray(blobs.get("fixtures.json", b""))
    if changed_bytes:
        changed_bytes[0] = ord(" ")
    mutations["changed_input_digest"] = bool(changed_bytes and digest(bytes(changed_bytes)) != freeze.get("a01_files", {}).get("fixtures.json"))
    decision_name = "PASS_AUDIT_ONLY_SCOPED" if not errors and all(mutations.values()) else "FAIL_AUDIT_ONLY"
    result = {
        "schema": "issue8502-t0-a02-audit-v1",
        "allocation": "A02",
        "decision": decision_name,
        "a01_decision_preserved": "FAIL_METHOD",
        "a01_auditor_defect": "between-group cumulative-category differences were computed as a difference of group maxima",
        "reconstructed_classes": {entry["fixture_id"]: entry["classification"] for entry in candidate.get("results", [])},
        "errors": errors,
        "mutation_rejections": mutations,
        "scope": "read-only independent audit of saved synthetic screening outputs; not psychometric or human-data evidence",
        "a01_artifact_sha256": {name: digest(raw) for name, raw in sorted(blobs.items())},
    }
    encoded = (json.dumps(result, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n").encode("utf-8")
    with (root / "AUDIT.json").open("xb") as stream:
        stream.write(encoded)
    print(json.dumps({"decision": decision_name, "errors": errors, "mutation_rejections": mutations, "audit_sha256": digest(encoded)}, sort_keys=True))


if __name__ == "__main__":
    main()
