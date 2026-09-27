#!/usr/bin/env python3
"""Independent CPU audit of source/template provenance and formal predictions."""
import argparse
import hashlib
import json
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path


HERE = Path(__file__).resolve().parent
TRAIN_FAMILIES = tuple(f"T{i:02d}" for i in range(1, 9))
HELDOUT_FAMILIES = tuple(f"T{i:02d}" for i in range(9, 13))
SEEDS = (29121, 29122, 29123)
ARMS = ("narrow_2_families", "broad_8_families")


def sha256(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")


def expected_point(box, dx, dy):
    x, y, width, height = box
    raw = [4 * (x + dx + width // 2), 4 * (y + dy + height // 2)]
    return [((value + 4) // 8) * 8 for value in raw]


def audit_sources(manifest, specs, image_root, expected_manifest_sha, expected_generator_sha):
    errors = []
    if sha256(canonical(manifest)) != expected_manifest_sha:
        errors.append("manifest_sha256_mismatch")
    if manifest.get("generator_sha256") != expected_generator_sha:
        errors.append("generator_sha256_mismatch")
    if manifest.get("template_spec_sha256") != sha256(canonical(specs)):
        errors.append("template_spec_file_hash_mismatch")
    if manifest.get("format") != "synthetic-form-grounding-source-manifest-v1":
        errors.append("manifest_format_mismatch")
    expected_renderer = {"pillow": "10.4.0", "template_unit_canvas": [320, 200],
                         "logical_canvas": [640, 400], "source_canvas": [1280, 800],
                         "source_scale": 2, "model_input": [160, 100],
                         "font": "Pillow ImageFont.load_default(size=18)",
                         "resample_source": "NEAREST", "resample_model": "BILINEAR"}
    if manifest.get("renderer") != expected_renderer:
        errors.append("renderer_metadata_mismatch")
    spec_rows = {row["id"]: row for row in specs.get("families", [])}
    family_rows = {row["family_id"]: row for row in manifest.get("families", [])}
    if set(spec_rows) != set(family_rows):
        errors.append("family_id_set_mismatch")
    records = manifest.get("records", [])
    if len(records) != 240:
        errors.append("record_count_mismatch")
    hashes, ids, counts = set(), set(), Counter()
    family_specs = {}
    for family_id, spec in spec_rows.items():
        digest = sha256(canonical(spec))
        family_specs[family_id] = digest
        observed = family_rows.get(family_id, {})
        if observed.get("spec_sha256") != digest:
            errors.append(f"template_spec_hash_mismatch:{family_id}")
        if observed.get("split") != spec.get("split"):
            errors.append(f"family_split_mismatch:{family_id}")
    if len({family_specs.get(f) for f in TRAIN_FAMILIES}) != 8:
        errors.append("train_template_sources_not_independent")
    if len({family_specs.get(f) for f in HELDOUT_FAMILIES}) != 4:
        errors.append("heldout_template_sources_not_independent")
    if set(TRAIN_FAMILIES) & set(HELDOUT_FAMILIES):
        errors.append("template_family_split_overlap")

    for record in records:
        record_id = record.get("record_id")
        family_id = record.get("family_id")
        if record_id in ids:
            errors.append(f"duplicate_record_id:{record_id}")
        ids.add(record_id)
        counts[family_id] += 1
        spec = spec_rows.get(family_id)
        if spec is None:
            errors.append(f"unknown_template_family:{family_id}")
            continue
        if record.get("split") != spec["split"]:
            errors.append(f"record_split_mismatch:{record_id}")
        if record.get("template_spec_sha256") != family_specs[family_id]:
            errors.append(f"record_template_sha256_mismatch:{record_id}")
        variant = record.get("variant")
        if type(variant) is not int or not 0 <= variant < 20:
            errors.append(f"invalid_variant:{record_id}")
            continue
        rng = random.Random(29120000 + int(family_id[1:]) * 1000 + variant)
        dx, dy = rng.choice([-4, -2, 0, 2, 4]), rng.choice([-2, 0, 2, 4])
        if record.get("field_point") != expected_point(spec["field"], dx, dy):
            errors.append(f"field_label_mismatch:{record_id}")
        if record.get("submit_point") != expected_point(spec["submit"], dx, dy):
            errors.append(f"submit_label_mismatch:{record_id}")
        for point in (record.get("field_point", []), record.get("submit_point", [])):
            if (len(point) != 2 or any(type(value) is not int for value in point) or
                    point[0] % 8 or point[1] % 8 or
                    not 0 <= point[0] < 1280 or not 0 <= point[1] < 800):
                errors.append(f"invalid_coordinate_grid:{record_id}")
        image_path = image_root / record.get("image", "")
        try:
            raw = image_path.read_bytes()
        except OSError:
            errors.append(f"missing_image:{record_id}")
            continue
        digest = sha256(raw)
        if digest != record.get("image_sha256"):
            errors.append(f"image_sha256_mismatch:{record_id}")
        if digest in hashes:
            errors.append(f"duplicate_image_content:{record_id}")
        hashes.add(digest)
    if set(counts) != set(spec_rows) or any(counts[family] != 20 for family in spec_rows):
        errors.append("per_family_record_count_mismatch")
    return errors


def audit_predictions(result, manifest, validate):
    errors = []
    records = {row["record_id"]: row for row in manifest["records"]}
    predictions = result.get("predictions", [])
    expected_count = len(SEEDS) * len(ARMS) * 4 * 20
    if result.get("formal_invocations") != 1 or result.get("retries") != 0:
        errors.append("formal_invocation_count_mismatch")
    if result.get("models") != len(SEEDS) * len(ARMS) or result.get("training_steps_per_model") != 500:
        errors.append("training_allocation_shape_mismatch")
    model_runs = result.get("model_runs", [])
    expected_runs = {(seed, arm) for seed in SEEDS for arm in ARMS}
    observed_runs = set()
    for run in model_runs:
        key = (run.get("seed"), run.get("arm"))
        if key in observed_runs:
            errors.append(f"duplicate_model_run:{key}")
        observed_runs.add(key)
        expected_families = TRAIN_FAMILIES if run.get("arm") == "broad_8_families" else ("T01", "T02")
        if (run.get("training_families") != list(expected_families) or
                run.get("optimizer_steps") != 500 or run.get("sampled_examples") != 8000 or
                run.get("unique_training_images") != len(expected_families) * 20 or
                not isinstance(run.get("train_seconds"), (int, float)) or run["train_seconds"] < 0 or
                not isinstance(run.get("first_sampled_batch_loss"), (int, float)) or
                not isinstance(run.get("last_sampled_batch_loss"), (int, float)) or
                not isinstance(run.get("peak_cuda_allocated_bytes"), int) or run["peak_cuda_allocated_bytes"] <= 0):
            errors.append(f"model_run_metadata_mismatch:{key}")
    if observed_runs != expected_runs:
        errors.append("model_run_key_set_mismatch")
    if len(predictions) != expected_count:
        errors.append("prediction_count_mismatch")
    seen = set()
    per_seed_family = defaultdict(lambda: {"exact": 0, "count": 0})
    per_arm = defaultdict(lambda: {"exact": 0, "count": 0, "schema_valid": 0, "schema_total": 0})
    false_schema = 0
    for row in predictions:
        key = (row.get("seed"), row.get("arm"), row.get("record_id"))
        if key in seen:
            errors.append(f"duplicate_prediction:{key}")
        seen.add(key)
        seed, arm, record_id = key
        if seed not in SEEDS or arm not in ARMS:
            errors.append(f"unknown_seed_or_arm:{key}")
            continue
        record = records.get(record_id)
        if record is None or record["split"] != "heldout" or record["family_id"] != row.get("family_id"):
            errors.append(f"prediction_not_frozen_heldout:{key}")
            continue
        if row.get("image_sha256") != record["image_sha256"]:
            errors.append(f"prediction_source_hash_mismatch:{key}")
        gold = record["field_point"] + record["submit_point"]
        if row.get("gold_points") != gold:
            errors.append(f"prediction_gold_mismatch:{key}")
        predicted = row.get("predicted_points")
        if (not isinstance(predicted, list) or len(predicted) != 4 or
                any(type(value) is not int for value in predicted)):
            errors.append(f"invalid_predicted_points:{key}")
            continue
        candidate = row.get("candidate")
        try:
            candidate_prediction = [candidate["field"]["point"]["x"], candidate["field"]["point"]["y"],
                                   candidate["submit"]["point"]["x"], candidate["submit"]["point"]["y"]]
        except (TypeError, KeyError):
            errors.append(f"candidate_point_shape_mismatch:{key}")
            candidate_prediction = None
        if candidate_prediction != predicted:
            errors.append(f"candidate_prediction_mismatch:{key}")
        per_arm[arm]["schema_total"] += 1
        try:
            validated = validate(candidate)
            actual_points = validated["field_point"] + validated["submit_point"]
            if actual_points != predicted:
                errors.append(f"candidate_prediction_mismatch:{key}")
            if row.get("validator") != "accept" or row.get("validator_points") != actual_points:
                errors.append(f"validator_receipt_mismatch:{key}")
            per_arm[arm]["schema_valid"] += 1
        except Exception:
            false_schema += 1
            if row.get("validator") != "reject" or not row.get("validator_error"):
                errors.append(f"invalid_candidate_not_rejected:{key}")
            if row.get("validator_points") is not None:
                errors.append(f"invalid_candidate_has_validated_points:{key}")
        exact = predicted == gold
        if row.get("exact_coordinates") is not exact:
            errors.append(f"exactness_flag_mismatch:{key}")
        per_seed_family[(seed, arm, record["family_id"])]["count"] += 1
        per_seed_family[(seed, arm, record["family_id"])]["exact"] += int(exact)
        per_arm[arm]["count"] += 1
        per_arm[arm]["exact"] += int(exact)

    required = {(seed, arm, record["record_id"])
                for seed in SEEDS for arm in ARMS for record in manifest["records"] if record["split"] == "heldout"}
    if seen != required:
        errors.append("prediction_key_set_mismatch")
    family_rates = {}
    for seed in SEEDS:
        for arm in ARMS:
            for family in HELDOUT_FAMILIES:
                item = per_seed_family[(seed, arm, family)]
                if item["count"] != 20:
                    errors.append(f"family_denominator_mismatch:{seed}:{arm}:{family}")
                family_rates[f"{seed}/{arm}/{family}"] = item["exact"] / item["count"] if item["count"] else 0.0
    arm_summary = {}
    for arm in ARMS:
        item = per_arm[arm]
        arm_summary[arm] = {"exact": item["exact"], "count": item["count"],
                            "exact_rate": item["exact"] / item["count"] if item["count"] else 0.0,
                            "schema_valid": item["schema_valid"], "schema_total": item["schema_total"],
                            "schema_valid_rate": item["schema_valid"] / item["schema_total"] if item["schema_total"] else 0.0}

    broad_family_rates = [
        sum(per_seed_family[(seed, "broad_8_families", family)]["exact"]
            for seed in SEEDS) / (20 * len(SEEDS))
        for family in HELDOUT_FAMILIES]
    improvement = arm_summary["broad_8_families"]["exact_rate"] - arm_summary["narrow_2_families"]["exact_rate"]
    if errors:
        disposition = "HOLD_AUDIT_INTEGRITY_ERRORS"
    elif any(summary["schema_valid_rate"] != 1.0 for summary in arm_summary.values()):
        disposition = "FAIL_SCHEMA_BOUNDS_VALIDITY"
    elif any(rate < 0.90 for rate in broad_family_rates):
        disposition = "FAIL_HELDOUT_COORDINATE_QUALITY"
    elif improvement < 0.10:
        disposition = "HOLD_NO_CLEAR_DIVERSITY_BENEFIT"
    else:
        disposition = "PASS_TEMPLATE_DIVERSITY_BENEFIT"
    return {"audit_status": "PASS" if not errors else "FAIL",
            "integrity_errors": errors, "disposition": disposition,
            "arm_summary": arm_summary, "broad_heldout_family_rates": dict(zip(HELDOUT_FAMILIES, broad_family_rates)),
            "broad_minus_narrow_exact_rate": improvement, "seed_arm_family_exact_rates": family_rates,
            "predictions": len(predictions), "accepted_schema_invalid": false_schema,
            "scope": "synthetic source-template heldout only; independent scorer, no GUI/action"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=HERE.parents[2])
    parser.add_argument("--result", type=Path, default=HERE / "results/formal01/results.json")
    args = parser.parse_args()
    repo = args.repo.resolve()
    root = repo / "research/analysis/gpu_grounding_template_diversity_2912_v2"
    freeze = json.loads((root / "FREEZE.json").read_text(encoding="utf-8"))
    source_paths = {
        ".gitattributes": root / ".gitattributes",
        "README.md": root / "README.md",
        "generate_corpus.py": root / "generate_corpus.py",
        "templates.json": root / "templates.json",
        "train_eval.py": root / "train_eval.py",
        "audit.py": root / "audit.py",
        "test_construction.py": root / "test_construction.py",
        "PREREGISTRATION.md": root / "PREREGISTRATION.md",
        "compiled_form_grounding_v1.py": repo / "research/live_control/compiled_form_grounding_v1.py",
        "compiled_form_grounding_schema_v1.json": repo / "research/live_control/compiled_form_grounding_schema_v1.json",
    }
    source_errors = [f"frozen_source_hash_mismatch:{name}"
                     for name, path in source_paths.items()
                     if sha256(path.read_bytes().replace(b"\r\n", b"\n")) != freeze["source_hashes"].get(name)]
    manifest = json.loads((root / "corpus/manifest.json").read_bytes())
    specs = json.loads((root / "templates.json").read_bytes())
    result = json.loads(args.result.read_bytes())
    if result.get("source_commit") != freeze.get("source_commit"):
        source_errors.append("source_commit_mismatch")
    if result.get("manifest_sha256") != freeze.get("manifest_sha256"):
        source_errors.append("result_manifest_sha256_mismatch")
    if result.get("runner_sha256") != freeze.get("runner_sha256"):
        source_errors.append("result_runner_sha256_mismatch")
    if result.get("source_hashes") != freeze.get("source_hashes"):
        source_errors.append("result_source_hashes_mismatch")
    environment = result.get("environment", {})
    if (environment.get("python") != "3.11.9" or environment.get("numpy") != "2.4.6" or
            environment.get("pillow") != "10.4.0" or environment.get("torch") != "2.5.1+cu121" or
            environment.get("cuda") != "12.1" or
            "RTX 3080" not in environment.get("device", "") or
            environment.get("cublas_workspace_config") != ":4096:8" or
            environment.get("execution_boundary") != "PC-local Windows host CUDA; pre-existing Docker image was CPU-only"):
        source_errors.append("formal_environment_mismatch")
    source_errors += audit_sources(manifest, specs, root / "corpus",
                                   freeze["manifest_sha256"], freeze["generator_sha256"])
    sys.path.insert(0, str(repo / "research/live_control"))
    from compiled_form_grounding_v1 import validate
    report = audit_predictions(result, manifest, validate)
    report["integrity_errors"] = source_errors + report["integrity_errors"]
    if source_errors:
        report["audit_status"] = "FAIL"
        report["disposition"] = "HOLD_AUDIT_INTEGRITY_ERRORS"
    report["manifest_sha256"] = freeze["manifest_sha256"]
    report["results_sha256"] = sha256(args.result.read_bytes())
    report_path = args.result.parent / "AUDIT.json"
    report_path.write_text(json.dumps(report, sort_keys=True, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({"audit_status": report["audit_status"], "disposition": report["disposition"],
                      "integrity_errors": report["integrity_errors"],
                      "arm_summary": report["arm_summary"]}, sort_keys=True))
    if report["audit_status"] != "PASS":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
