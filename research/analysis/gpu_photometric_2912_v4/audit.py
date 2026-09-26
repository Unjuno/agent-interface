#!/usr/bin/env python3
"""Independent source, routing, schema, and outcome audit for one result."""
import hashlib
import json
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image


MANIFEST_SHA = "dc86185fdec9a1605548861519fa6777c1153948c032c49a7fa1557160c77bc8"
IMAGE_SHA = {
    "task-1": "3fd0c515a1f0358fb4afa328f60d2a1b82a748018ff4295fad5ec3922f3640ec",
    "task-2": "8ce9f5bdb642592122e0f7ed2c84656729564ced3d25c14af6b787c71ef8ce7a",
    "task-3": "3e81cc92439d01aeabd69c8cfd9f2a2eb842b3433f41771fe3b0409e331f9349",
    "task-4": "ae2974269932d767fbfba536287c2f8c02c1ffb77efaed6c3c87b20c250fbad4",
    "task-5": "7216758322e41ff158751f70623401089df7080011fdac5c9ea59ea7b49b559a",
    "task-6": "ccc8662251de86ee477e8ff149ce19c67de8e26bb93f5ead264fe268438118bd",
}
TRAIN = ("task-1", "task-2", "task-4", "task-5")
HELD = ("task-3", "task-6")
TRANSFORMS = (("original", 1.0), ("dark_0.85", 0.85), ("bright_1.15", 1.15))


def digest(data):
    return hashlib.sha256(data).hexdigest()


def expected_pooling_matrix_sha256():
    def matrix(source, target):
        values = np.zeros((target, source), dtype=np.float32)
        for out_index in range(target):
            start = (out_index * source) // target
            end = ((out_index + 1) * source + target - 1) // target
            values[out_index, start:end] = 1.0 / (end - start)
        return values
    return digest(matrix(25, 8).tobytes() + matrix(40, 10).tobytes())


def variant_hash(repo, rec, factor):
    with Image.open(repo / rec["image"]) as im:
        arr = np.asarray(im.convert("RGB"), dtype=np.uint8)
    if factor != 1.0:
        arr = np.clip(np.floor(arr.astype(np.float32) * factor + 0.5), 0, 255).astype(np.uint8)
    return digest(arr.tobytes())


def expected_route(logits):
    if len(logits) != 2 or any(not math.isfinite(float(v)) for v in logits):
        raise ValueError("invalid raw logits")
    maximum = max(float(v) for v in logits)
    exps = [math.exp(float(v) - maximum) for v in logits]
    total = sum(exps)
    probs = [v / total for v in exps]
    pred = max(range(2), key=lambda i: float(logits[i]))
    confidence = probs[pred]
    route = "accept" if confidence >= 0.75 else ("yield" if confidence >= 0.25 else "reject")
    return pred, confidence, route


def audit_file(repo, raw_path, audit_path):
    repo, raw_path, audit_path = map(Path, (repo, raw_path, audit_path))
    manifest_path = repo / "research/analysis/local_model_2912_image_manifest.json"
    raw_manifest = manifest_path.read_bytes()
    canonical_manifest = raw_manifest.replace(b"\r\n", b"\n")
    if digest(canonical_manifest) != MANIFEST_SHA:
        raise ValueError("source manifest hash mismatch")
    manifest = json.loads(canonical_manifest)
    rows = {r["task_id"]: r for r in manifest["records"]}
    if set(rows) != set(IMAGE_SHA):
        raise ValueError("source task set mismatch")
    for task, expected in IMAGE_SHA.items():
        actual = digest((repo / rows[task]["image"]).read_bytes())
        if actual != expected or rows[task]["image_sha256"] != expected:
            raise ValueError(f"source image mismatch: {task}")

    raw = json.loads(raw_path.read_text(encoding="utf-8"))
    if raw.get("format") != "gpu-photometric-2912-v4-result-v1":
        raise ValueError("result format mismatch")
    if raw.get("pooling_operator") != "deterministic_adaptive_avg_pool2d_separable_hw25x40_v1":
        raise ValueError("pooling operator mismatch")
    if raw.get("source_commit") != "21dd6a26dbd9f5cb4a6e11b1060902799a76a733":
        raise ValueError("source commit mismatch")
    if raw.get("cnn_feature_map_shape") != [16, 16, 25, 40]:
        raise ValueError("CNN feature-map shape identity mismatch")
    if raw.get("pooling_matrix_sha256") != expected_pooling_matrix_sha256():
        raise ValueError("pooling matrix identity mismatch")
    environment = raw.get("environment", {})
    if (environment.get("deterministic_algorithms") is not True or
            environment.get("cudnn_deterministic") is not True or
            environment.get("cudnn_benchmark") is not False or
            environment.get("tf32_matmul") is not False or
            environment.get("cublas_workspace_config") != ":4096:8"):
        raise ValueError("deterministic environment gate mismatch")
    freeze_path = Path(__file__).with_name("FREEZE.json")
    freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
    if (freeze.get("schema") != "gpu-photometric-2912-v4-freeze-v1" or
            freeze.get("formal_invocations_allowed") != 1 or
            freeze.get("formal_invocations_completed_before_freeze") != 0 or
            freeze.get("formal_result_exists") is not False):
        raise ValueError("freeze allocation identity/status mismatch")
    if (freeze.get("source_commit") != raw.get("source_commit") or
            freeze.get("manifest_sha256") != raw.get("manifest_sha256") or
            freeze.get("image_sha256") != raw.get("image_sha256")):
        raise ValueError("raw sources differ from frozen allocation")
    if raw.get("runner_sha256") != freeze.get("runner_sha256"):
        raise ValueError("runner hash differs from frozen source")
    if digest(Path(__file__).read_bytes().replace(b"\r\n", b"\n")) != freeze.get("audit_sha256"):
        raise ValueError("audit source differs from freeze")
    for field, name in (("preregistration_sha256", "PREREGISTRATION.md"),
                        ("construction_sha256", "CONSTRUCTION.md"),
                        ("construction_test_sha256", "test_construction.py"),
                        ("audit_control_test_sha256", "test_audit_controls.py")):
        path = Path(__file__).with_name(name)
        if digest(path.read_bytes().replace(b"\r\n", b"\n")) != freeze.get(field):
            raise ValueError(f"{name} source differs from freeze")
    if raw.get("manifest_sha256") != MANIFEST_SHA or raw.get("image_sha256") != IMAGE_SHA:
        raise ValueError("result source identity mismatch")
    expected_schedule = {"seed": 3926, "steps": 300, "batch_size": 16,
                         "training_brightness_range": [0.70, 1.30],
                         "evaluation_factors": [1.0, 0.85, 1.15]}
    if raw.get("schedule") != expected_schedule:
        raise ValueError("training/evaluation schedule mismatch")
    if raw.get("split") != {"train": list(TRAIN), "held_out": list(HELD)}:
        raise ValueError("result split mismatch")
    if len(raw.get("arms", [])) != 2:
        raise ValueError("two arms required")

    sys.path.insert(0, str(repo / "research/live_control"))
    from compiled_form_grounding_v1 import validate

    arm_summaries = []
    arm_exact = {}
    arm_case_exact = {}
    expected_train_hashes = {
        task: variant_hash(repo, rows[task], 1.0) for task in TRAIN
    }
    for arm, expected_name, expected_aug in zip(
            raw["arms"], ("no_augmentation", "brightness_augmentation"), (False, True)):
        if arm.get("arm") != expected_name or arm.get("brightness_augmentation") is not expected_aug:
            raise ValueError("arm identity/order mismatch")
        if tuple(arm.get("train_task_ids", [])) != TRAIN:
            raise ValueError("arm training rows mismatch")
        if arm.get("optimizer_steps") != 300:
            raise ValueError("optimizer step count mismatch")
        if arm.get("train_source_hashes") != expected_train_hashes:
            raise ValueError("training source hashes mismatch")
        predictions = arm.get("predictions", [])
        expected_keys = {(task, transform) for task in HELD for transform, _ in TRANSFORMS}
        actual_keys = {(p.get("task_id"), p.get("transform")) for p in predictions}
        if len(predictions) != 6 or actual_keys != expected_keys:
            raise ValueError("evaluation key/count mismatch")
        counts = {"exact": 0, "accepted": 0, "accepted_false": 0,
                  "yield": 0, "reject": 0, "validator_accept": 0}
        exact_by_transform = {transform: 0 for transform, _ in TRANSFORMS}
        exact_by_case = {}
        wrong = []
        for pred in predictions:
            task = pred["task_id"]
            rec = rows[task]
            factor = dict(TRANSFORMS)[pred["transform"]]
            if pred.get("factor") != factor or pred.get("true_layout") != rec["layout"]:
                raise ValueError("eval label/transform mismatch")
            if pred.get("input_sha256") != variant_hash(repo, rec, factor):
                raise ValueError("transformed eval image hash mismatch")
            index, confidence, route = expected_route(pred.get("logits", []))
            layout = ("A", "B")[index]
            if pred.get("predicted_layout") != layout:
                raise ValueError("prediction differs from logits")
            if not math.isclose(float(pred.get("top_class_confidence")), confidence,
                                rel_tol=1e-6, abs_tol=1e-7):
                raise ValueError("confidence mismatch")
            if pred.get("route") != route:
                raise ValueError("routing mismatch")
            try:
                points = validate(pred["candidate"])
            except Exception as exc:
                raise ValueError(f"compiled validator rejected candidate: {exc}") from exc
            counts["validator_accept"] += 1
            expected_points = {"field_point": rec["field_point"],
                               "submit_point": rec["submit_point"]}
            exact = (points["field_point"] == expected_points["field_point"] and
                     points["submit_point"] == expected_points["submit_point"])
            if pred.get("validator_points") != points or pred.get("exact_coordinates") is not exact:
                raise ValueError("candidate/oracle mismatch")
            counts["exact"] += int(exact)
            exact_by_transform[pred["transform"]] += int(exact)
            case_key = f"{task}|{pred['transform']}"
            exact_by_case[case_key] = int(exact)
            counts["accepted"] += int(route == "accept")
            counts["yield"] += int(route == "yield")
            counts["reject"] += int(route == "reject")
            counts["accepted_false"] += int(route == "accept" and not exact)
            if not exact:
                wrong.append({"task_id": task, "transform": pred["transform"],
                              "predicted_layout": layout, "true_layout": rec["layout"],
                              "route": route})
        arm_exact[expected_name] = exact_by_transform
        arm_case_exact[expected_name] = exact_by_case
        arm_summaries.append({"arm": expected_name, **counts,
                              "exact_by_transform": exact_by_transform,
                              "wrong_predictions": wrong,
                              "train_seconds": arm.get("train_seconds"),
                              "peak_cuda_bytes": arm.get("peak_cuda_bytes")})

    a, b = arm_summaries
    perturbed = ("dark_0.85", "bright_1.15")
    perturbed_cases = [
        f"{task}|{transform}"
        for task in HELD for transform in perturbed
    ]
    per_case_exact = {
        name: {
            f"{task}|{transform}": arm_case_exact[name][f"{task}|{transform}"]
            for task in HELD for transform in perturbed
        }
        for name in ("no_augmentation", "brightness_augmentation")
    }
    base_perturbed = sum(per_case_exact["no_augmentation"].values())
    aug_perturbed = sum(per_case_exact["brightness_augmentation"].values())
    no_case_regression = all(
        per_case_exact["brightness_augmentation"][case] >=
        per_case_exact["no_augmentation"][case]
        for case in perturbed_cases
    )
    strict_case_gain = any(
        per_case_exact["brightness_augmentation"][case] >
        per_case_exact["no_augmentation"][case]
        for case in perturbed_cases
    )
    no_accepted_false = all(x["accepted_false"] == 0 for x in arm_summaries)
    aug_gate = no_accepted_false and no_case_regression and strict_case_gain
    accepted_wrong = any(x["accepted_false"] for x in arm_summaries)
    status = ("FAIL_ACCEPTED_FALSE_GROUNDING" if accepted_wrong else
              "PASS_PHOTOMETRIC_AUGMENTATION_SCOPED" if aug_gate else "HOLD_NO_SAFE_BENEFIT")
    audit = {
        "format": "gpu-photometric-grounding-independent-audit-v1",
        "status": status,
        "source_manifest_sha256": digest(canonical_manifest),
        "source_images_verified": len(IMAGE_SHA),
        "heldout_rows_per_arm": 6,
        "perturbed_exact": {"no_augmentation": base_perturbed,
                             "brightness_augmentation": aug_perturbed,
                             "max": 4,
                             "per_case": per_case_exact,
                             "no_case_regression": no_case_regression,
                             "strict_case_gain": strict_case_gain},
        "arms": arm_summaries,
        "validator_scope": "schema/bounds only; coordinate correctness independently recomputed from source manifest",
        "scope": "two held-out source images only; no GUI/action/authority/runtime claim",
    }
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    audit_path.write_text(json.dumps(audit, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(audit, sort_keys=True, indent=2))
    return audit


def main():
    if len(sys.argv) != 4:
        raise SystemExit("usage: audit.py REPO_ROOT RESULTS_JSON AUDIT_JSON")
    audit_file(*sys.argv[1:])


if __name__ == "__main__":
    main()
