#!/usr/bin/env python3
"""Independent audit supplement for retained Issue #4561 results.

This module intentionally uses only the standard library and derives labels
from the frozen corpus manifest, never from result-row self-reports.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
from collections import Counter, defaultdict
from pathlib import PurePosixPath


SEEDS = (456101, 456102, 456103)
ARMS = ("narrow_2_families", "broad_8_families")
HELDOUT = ("family-09", "family-10", "family-11", "family-12")
ACCEPT_MIN = 0.75
EXPECTED_MANIFEST_SHA256 = "7e4958551a229d75ba8da8fe23fb47b7c013d3228a7c6aabf745848b5004c9f7"
EXPECTED_RAW_SHA256 = "5ff992341e4f28357a4b0bdd1166d7c2a33e1aadab80fd8b576500c3a3b9fe97"
BASE = "research/analysis/gpu_grounding_template_diversity_2912_v2"
RAW_PATH = f"{BASE}/results/formal01/results.json"
MANIFEST_PATH = f"{BASE}/corpus_manifest.json"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _cell(value):
    return (isinstance(value, list) and len(value) == 2 and
            all(type(x) is int for x in value) and 0 <= value[0] < 8 and 0 <= value[1] < 10)


def audit_data(raw, manifest):
    errors = []
    images = manifest.get("images", [])
    expected_images = {}
    for image in images:
        image_id = image.get("image_id")
        if not isinstance(image_id, str) or image_id in expected_images:
            errors.append("manifest image IDs are missing or duplicated")
            continue
        expected_images[image_id] = image
    eval_images = {k: v for k, v in expected_images.items() if v.get("family_id") in HELDOUT}
    wanted_image_ids = {f"{family}/variant-{variant}" for family in HELDOUT for variant in range(4)}
    if set(eval_images) != wanted_image_ids or len(images) != 48:
        errors.append("frozen manifest evaluation population mismatch")

    cases = raw.get("cases", [])
    wanted = {(seed, arm, image_id) for seed in SEEDS for arm in ARMS for image_id in wanted_image_ids}
    seen = set()
    counts = Counter()
    family_counts = Counter()
    yielded = 0
    accepted_wrong = 0
    target_matches = 0
    for row in cases:
        seed, arm, image_id = row.get("seed"), row.get("arm"), row.get("image_id")
        key = (seed, arm, image_id)
        if key in seen:
            errors.append("duplicate seed/arm/image case")
        seen.add(key)
        if key not in wanted:
            errors.append("case outside exact frozen seed/arm/image population")
        expected = eval_images.get(image_id)
        if expected is None:
            errors.append("unknown or non-held-out image ID")
            continue
        if row.get("family_id") != expected.get("family_id"):
            errors.append("family ID disagrees with frozen image manifest")
        target = [expected.get("field_cell"), expected.get("submit_cell")]
        points = [expected.get("field_point"), expected.get("submit_point")]
        if row.get("target_cells") != target:
            errors.append("self-reported target cells disagree with frozen manifest")
        else:
            target_matches += 1
        if row.get("target_points") != points:
            errors.append("self-reported target points disagree with frozen manifest")
        pred = row.get("predicted_cells")
        if not isinstance(pred, list) or len(pred) != 2 or not all(_cell(c) for c in pred):
            errors.append("invalid predicted cell pair")
            continue
        correct = pred == target
        if row.get("exact_pair_correct") is not correct:
            errors.append("self-reported exact correctness disagrees with manifest-derived score")
        confidence = row.get("confidence")
        if (not isinstance(confidence, list) or len(confidence) != 2 or
                any(type(x) not in (int, float) or not math.isfinite(x) or not 0 <= x <= 1 for x in confidence)):
            errors.append("invalid confidence pair")
            continue
        accepted = min(confidence) >= ACCEPT_MIN
        if row.get("accepted") is not accepted:
            errors.append("accept/YIELD decision disagrees with frozen threshold")
        if accepted:
            if row.get("candidate_valid") is not True or not isinstance(row.get("parsed_candidate"), dict):
                errors.append("accepted proposal lacks validator evidence")
        elif row.get("candidate_valid") is not False or row.get("parsed_candidate") is not None:
            errors.append("yielded row emitted a candidate")
        wrong = accepted and not correct
        if row.get("accepted_wrong") is not wrong:
            errors.append("accepted-wrong field disagrees with independent score")
        counts[arm, "n"] += 1
        counts[arm, "correct"] += int(correct)
        counts[arm, "accepted"] += int(accepted)
        counts[arm, "accepted_wrong"] += int(wrong)
        family_counts[arm, expected["family_id"], "n"] += 1
        family_counts[arm, expected["family_id"], "correct"] += int(correct)
        yielded += int(not accepted)
        accepted_wrong += int(wrong)

    if seen != wanted:
        errors.append("missing or extra seed/arm/image cases")
    if len(cases) != 96 or len(seen) != 96:
        errors.append("case cardinality is not exactly 96")
    metrics = {arm: {"cases": counts[arm, "n"], "exact": counts[arm, "correct"],
                     "accuracy": counts[arm, "correct"] / counts[arm, "n"] if counts[arm, "n"] else 0,
                     "accepted": counts[arm, "accepted"],
                     "accepted_wrong": counts[arm, "accepted_wrong"]} for arm in ARMS}
    by_family = {arm: {family: {"cases": family_counts[arm, family, "n"],
                                "exact": family_counts[arm, family, "correct"]}
                       for family in HELDOUT} for arm in ARMS}
    delta = metrics[ARMS[1]]["accuracy"] - metrics[ARMS[0]]["accuracy"]
    if not errors:
        if (metrics[ARMS[1]]["accepted_wrong"] == 0 and
                all(by_family[ARMS[1]][f]["cases"] == 12 and
                    by_family[ARMS[1]][f]["exact"] / 12 >= 0.90 for f in HELDOUT) and delta >= 0.10):
            status = "PASS_TEMPLATE_DIVERSITY_SCOPED"
        else:
            status = "HOLD_OR_FAIL_FROZEN_GATES_NOT_MET"
    else:
        status = "HOLD_AUDIT_INTEGRITY"
    return {"status": status, "errors": errors, "cases_checked": len(cases),
            "manifest_target_matches": target_matches, "yielded_cases": yielded,
            "accepted_wrong_coordinates": accepted_wrong, "metrics": metrics,
            "exact_by_heldout_family": by_family, "broad_minus_narrow": delta}


def audit_bytes(raw_bytes: bytes, manifest_bytes: bytes):
    raw_hash, manifest_hash = sha256(raw_bytes), sha256(manifest_bytes)
    errors = []
    if raw_hash != EXPECTED_RAW_SHA256:
        errors.append("raw results SHA-256 pin mismatch")
    if manifest_hash != EXPECTED_MANIFEST_SHA256:
        errors.append("corpus manifest SHA-256 pin mismatch")
    try:
        raw = json.loads(raw_bytes)
        manifest = json.loads(manifest_bytes)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        return {"status": "STOP_INPUT_BYTES_MISMATCH", "errors": errors + [f"invalid JSON: {exc}"]}
    result = audit_data(raw, manifest)
    if errors:
        result["errors"] = errors + result["errors"]
        result["status"] = "STOP_INPUT_BYTES_MISMATCH"
    result["input_sha256"] = {"raw_results": raw_hash, "corpus_manifest": manifest_hash}
    return result


def read_git_blob(repository, ref, path):
    return subprocess.check_output(["git", "-C", str(repository), "show", f"{ref}:{path}"])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True, help="local Git repository containing fetched main")
    parser.add_argument("--ref", default="origin/main")
    parser.add_argument("--output")
    args = parser.parse_args()
    raw = read_git_blob(args.repository, args.ref, RAW_PATH)
    manifest = read_git_blob(args.repository, args.ref, MANIFEST_PATH)
    result = audit_bytes(raw, manifest)
    encoded = json.dumps(result, sort_keys=True, indent=2) + "\n"
    if args.output:
        with open(args.output, "x", encoding="utf-8", newline="\n") as handle:
            handle.write(encoded)
    print(encoded, end="")
    return 0 if result["status"] == "HOLD_OR_FAIL_FROZEN_GATES_NOT_MET" and not result["errors"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
