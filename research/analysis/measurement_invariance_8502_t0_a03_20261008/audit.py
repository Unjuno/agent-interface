"""Independent raw-only auditor for Issue #8502 T0 A03; no candidate imports."""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from itertools import combinations
from math import sqrt
from pathlib import Path
from typing import Any

EXPECTED_SOURCES = {"README.md", "PROTOCOL.md", "CONSTRUCTION.md", "config.json", "generate.py", "candidate.py",
                    "integrity.py", "audit.py", "test_candidate.py", "test_audit.py", "freeze.py"}
EXPECTED_INPUTS = {"fixtures.json", "truth.json"}


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def raw_json(root: Path, name: str) -> tuple[bytes, Any]:
    raw = (root / name).read_bytes()
    return raw, json.loads(raw)


def identity_errors(root: Path, freeze: dict) -> list[str]:
    errors = []
    if set(freeze.get("sources", {})) != EXPECTED_SOURCES:
        errors.append("source_manifest_inventory")
    if set(freeze.get("inputs", {})) != EXPECTED_INPUTS:
        errors.append("input_manifest_inventory")
    if freeze.get("schema") != "issue8502-t0-a03-freeze-v1" or freeze.get("issue") != 8502 or freeze.get("allocation") != "A03":
        errors.append("freeze_identity")
    if len(freeze.get("main_sha", "")) != 40:
        errors.append("main_sha_shape")
    for section in ("sources", "inputs"):
        for name, expected in freeze.get(section, {}).items():
            path = root / name
            if not path.is_file() or digest(path.read_bytes()) != expected:
                errors.append(f"{section}_digest:{name}")
    return errors


def contingency_pearson(rows: list[list[int]], left: int, right: int) -> float:
    """Compute Pearson r from a 5x5 contingency table, not candidate row moments."""
    table = Counter((row[left], row[right]) for row in rows)
    n = len(rows)
    sx = sy = sxx = syy = sxy = 0
    for (x, y), count in table.items():
        sx += x * count
        sy += y * count
        sxx += x * x * count
        syy += y * y * count
        sxy += x * y * count
    vx = n * sxx - sx * sx
    vy = n * syy - sy * sy
    return 0.0 if vx <= 0 or vy <= 0 else (n * sxy - sx * sy) / sqrt(vx * vy)


def cdf_profile(rows: list[list[int]], item: int) -> list[float]:
    counts = Counter(row[item] for row in rows)
    n = len(rows)
    total = 0
    cdf = []
    for category in range(4):
        total += counts[category]
        cdf.append(total / n)
    return cdf


def independently_classify(fixture: dict, config: dict) -> tuple[dict, dict]:
    a, b = fixture["groups"]["A"], fixture["groups"]["B"]
    items = config["item_count"]
    if min(len(a), len(b)) < config["min_n_per_group"]:
        return ({"classification": "UNCERTAIN", "threshold_items": [], "loading_items": [], "association_edges": []},
                {"max_cutpoint_gaps": [], "association_edges": []})

    gaps = []
    for item in range(items):
        ca, cb = cdf_profile(a, item), cdf_profile(b, item)
        # Pair by ordinal threshold before taking the maximum; never subtract maxima.
        gaps.append(max(abs(x - y) for x, y in zip(ca, cb)))
    threshold_items = [item for item, gap in enumerate(gaps) if gap > config["threshold_margin"]]
    if threshold_items:
        decision = {"classification": "THRESHOLD_NONINVARIANCE", "threshold_items": threshold_items,
                    "loading_items": [], "association_edges": []}
        return decision, {"max_cutpoint_gaps": [round(value, 12) for value in gaps], "association_edges": []}

    changed = []
    for left, right in combinations(range(items), 2):
        delta = abs(contingency_pearson(a, left, right) - contingency_pearson(b, left, right))
        if delta > config["association_margin"]:
            changed.append(f"{left}-{right}")
    shared = set.intersection(*(set(map(int, edge.split("-"))) for edge in changed)) if changed else set()
    if not changed:
        label, localized = "COMPATIBLE_SCREEN", []
    elif len(changed) >= 3 and len(shared) == 1:
        label, localized = "LOADING_PATTERN_NONINVARIANCE", sorted(shared)
    else:
        label, localized = "STRUCTURE_NONINVARIANCE", []
    decision = {"classification": label, "threshold_items": [], "loading_items": localized,
                "association_edges": changed}
    return decision, {"max_cutpoint_gaps": [round(value, 12) for value in gaps], "association_edges": changed}


def semantic_errors(fixtures: dict, config: dict, truth: dict, candidate: dict) -> list[str]:
    errors = []
    actual = {row.get("fixture_id"): row for row in candidate.get("results", [])}
    fixture_rows = {row.get("fixture_id"): row for row in fixtures.get("fixtures", [])}
    expected_ids = set(config["expected"])
    if set(actual) != expected_ids or set(fixture_rows) != expected_ids:
        errors.append("fixture_result_set")
    params = {key: config[key] for key in ("min_n_per_group", "threshold_margin", "association_margin")}
    if candidate.get("parameters") != params:
        errors.append("parameters")
    if truth.get("cases") != config["expected"]:
        errors.append("truth_config")
    for name in sorted(expected_ids & set(actual) & set(fixture_rows)):
        reconstructed, diagnostics = independently_classify(fixture_rows[name], config)
        row = actual[name]
        expected = config["expected"][name]
        for field in ("classification", "threshold_items", "loading_items", "association_edges"):
            if row.get(field) != reconstructed[field]:
                errors.append(f"reconstruction:{name}:{field}")
        for field in ("classification", "threshold_items", "loading_items"):
            if row.get(field) != expected[field]:
                errors.append(f"truth:{name}:{field}")
        if row.get("diagnostics") != diagnostics:
            errors.append(f"diagnostics:{name}")
        if fixture_rows[name].get("seed") != config["seeds"].get(name):
            errors.append(f"seed:{name}")
    return errors


def mutation_controls(fixtures: dict, config: dict, truth: dict, candidate: dict, freeze: dict) -> dict[str, bool]:
    checks = {}
    changed = json.loads(json.dumps(candidate))
    changed["results"][0]["classification"] = "THRESHOLD_NONINVARIANCE"
    checks["wrong_class"] = bool(semantic_errors(fixtures, config, truth, changed))

    changed = json.loads(json.dumps(candidate))
    changed["results"][1]["threshold_items"] = [1]
    checks["wrong_threshold_localization"] = bool(semantic_errors(fixtures, config, truth, changed))

    changed = json.loads(json.dumps(candidate))
    changed["results"][-1]["classification"] = "COMPATIBLE_SCREEN"
    checks["sparse_accepted"] = bool(semantic_errors(fixtures, config, truth, changed))

    changed = json.loads(json.dumps(candidate))
    changed["results"].pop()
    checks["missing_result"] = bool(semantic_errors(fixtures, config, truth, changed))

    altered = json.loads(json.dumps(fixtures))
    altered["fixtures"][0]["seed"] += 1
    checks["wrong_seed"] = bool(semantic_errors(altered, config, truth, candidate))

    altered_bytes = bytearray(json.dumps(fixtures, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode() + b"\n")
    altered_bytes[0] ^= 1
    checks["tampered_input_digest"] = digest(bytes(altered_bytes)) != freeze["inputs"]["fixtures.json"]
    return checks


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", default=".")
    args = parser.parse_args()
    root = Path(args.dir).resolve()
    freeze_raw, freeze = raw_json(root, "FREEZE.json")
    _, fixtures = raw_json(root, "fixtures.json")
    _, config = raw_json(root, "config.json")
    _, truth = raw_json(root, "truth.json")
    candidate_raw, candidate = raw_json(root, "candidate.json")
    errors = identity_errors(root, freeze)
    if candidate.get("freeze_sha256") != digest(freeze_raw):
        errors.append("candidate_freeze_binding")
    if candidate.get("fixture_sha256") != digest((root / "fixtures.json").read_bytes()):
        errors.append("candidate_fixture_binding")
    if candidate.get("truth_sha256") != digest((root / "truth.json").read_bytes()):
        errors.append("candidate_truth_binding")
    errors.extend(semantic_errors(fixtures, config, truth, candidate))
    mutations = mutation_controls(fixtures, config, truth, candidate, freeze)
    result = {
        "schema": "issue8502-t0-a03-independent-audit-v1",
        "decision": "PASS_METHOD_SCOPED" if not errors and all(mutations.values()) else "FAIL_METHOD",
        "fixture_count": len(fixtures.get("fixtures", [])),
        "independent_errors": errors,
        "mutation_rejections": mutations,
        "artifact_sha256": {"FREEZE.json": digest(freeze_raw), "fixtures.json": digest((root / "fixtures.json").read_bytes()),
                            "truth.json": digest((root / "truth.json").read_bytes()), "candidate.json": digest(candidate_raw)},
        "scope": "fresh synthetic ordinal screening only; no human comparability claim",
    }
    encoded = (json.dumps(result, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n").encode()
    with (root / "AUDIT.json").open("xb") as stream:
        stream.write(encoded)
    print(json.dumps({"decision": result["decision"], "errors": errors, "mutation_rejections": mutations,
                      "audit_sha256": digest(encoded)}, sort_keys=True))


if __name__ == "__main__":
    main()
