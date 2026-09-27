import contextlib
import copy
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(REPO / "research/live_control"))

import audit
from compiled_form_grounding_v1 import validate


def candidate(layout, rows):
    record = next(row for row in rows.values() if row["layout"] == layout)
    def target(point):
        return {"point_space": "source_observation_pixels",
                "point": {"x": point[0], "y": point[1]},
                "motion_model": "surface_origin_translation"}
    return {"format": "compiled-form-grounding-v1",
            "field": target(record["field_point"]),
            "submit": target(record["submit_point"]),
            "method": {"first_action": "enter_exact_token",
                       "continue_when": "field_pixels_changed_and_submit_revalidated",
                       "second_action": "activate_submit",
                       "complete_when": "submission_pixels_changed_then_independent_score"}}


def fixture(repo):
    manifest = json.loads((repo / "research/analysis/local_model_2912_image_manifest.json").read_text())
    rows = {row["task_id"]: row for row in manifest["records"]}
    freeze = json.loads((HERE / "FREEZE.json").read_text())
    raw = {
        "format": "gpu-photometric-2912-v3-result-v1",
        "source_commit": freeze["source_commit"],
        "manifest_sha256": audit.MANIFEST_SHA,
        "image_sha256": audit.IMAGE_SHA,
        "split": {"train": list(audit.TRAIN), "held_out": list(audit.HELD)},
        "schedule": {"seed": 3926, "steps": 300, "batch_size": 16,
                     "training_brightness_range": [0.70, 1.30],
                     "evaluation_factors": [1.0, 0.85, 1.15]},
        "pooling_operator": "deterministic_adaptive_avg_pool2d_separable_v1",
        "pooling_matrix_sha256": audit.expected_pooling_matrix_sha256(),
        "runner_sha256": freeze["runner_sha256"],
        "environment": {"deterministic_algorithms": True, "cudnn_deterministic": True,
                        "cudnn_benchmark": False, "tf32_matmul": False,
                        "cublas_workspace_config": ":4096:8"},
        "arms": [],
    }
    for name, augmented in (("no_augmentation", False), ("brightness_augmentation", True)):
        arm = {"arm": name, "brightness_augmentation": augmented,
               "optimizer_steps": 300, "train_task_ids": list(audit.TRAIN),
               "train_source_hashes": {task: audit.variant_hash(repo, rows[task], 1.0)
                                        for task in audit.TRAIN},
               "train_seconds": 1.0, "peak_cuda_bytes": 4096, "predictions": []}
        for task in audit.HELD:
            row = rows[task]
            for transform, factor in audit.TRANSFORMS:
                idx = 0 if row["layout"] == "A" else 1
                logits = [8.0, -8.0] if idx == 0 else [-8.0, 8.0]
                pred_idx, confidence, route = audit.expected_route(logits)
                layout = ("A", "B")[pred_idx]
                points = validate(candidate(layout, rows))
                expected = {"field_point": row["field_point"],
                            "submit_point": row["submit_point"]}
                arm["predictions"].append({
                    "task_id": task, "true_layout": row["layout"],
                    "transform": transform, "factor": factor,
                    "input_sha256": audit.variant_hash(repo, row, factor),
                    "logits": logits, "predicted_layout": layout,
                    "top_class_confidence": confidence, "route": route,
                    "candidate": candidate(layout, rows), "validator_points": points,
                    "exact_coordinates": (points["field_point"] == expected["field_point"] and
                                          points["submit_point"] == expected["submit_point"]),
                })
        raw["arms"].append(arm)
    return raw, rows


def write_and_audit(raw):
    with tempfile.TemporaryDirectory(prefix="issue4470-audit-") as temp:
        root = Path(temp)
        result_path = root / "result.json"
        audit_path = root / "audit.json"
        result_path.write_text(json.dumps(raw, allow_nan=True), encoding="utf-8")
        with contextlib.redirect_stdout(io.StringIO()):
            result = audit.audit_file(REPO, result_path, audit_path)
        return result


def set_case(raw, rows, arm_index, task, transform, layout, confidence_band):
    arm = raw["arms"][arm_index]
    record = rows[task]
    row = next(p for p in arm["predictions"]
               if p["task_id"] == task and p["transform"] == transform)
    if confidence_band == "accept":
        logits = [8.0, -8.0] if layout == "A" else [-8.0, 8.0]
    else:
        logits = [0.1, 0.0] if layout == "A" else [0.0, 0.1]
    pred_idx, confidence, route = audit.expected_route(logits)
    layout = ("A", "B")[pred_idx]
    candidate_value = candidate(layout, rows)
    points = validate(candidate_value)
    row.update({"logits": logits, "predicted_layout": layout,
                "top_class_confidence": confidence, "route": route,
                "candidate": candidate_value, "validator_points": points,
                "exact_coordinates": (points["field_point"] == record["field_point"] and
                                      points["submit_point"] == record["submit_point"])})


class AuditControlTests(unittest.TestCase):
    def setUp(self):
        self.raw, self.rows = fixture(REPO)

    def assert_rejected(self, change):
        raw = copy.deepcopy(self.raw)
        change(raw)
        with self.assertRaises((ValueError, KeyError, TypeError)):
            write_and_audit(raw)

    def test_clean_fixture_is_audited_as_no_benefit(self):
        result = write_and_audit(self.raw)
        self.assertEqual(result["status"], "HOLD_NO_SAFE_BENEFIT")

    def test_effective_corruptions_reject(self):
        changes = [
            lambda x: x.update(format="wrong"),
            lambda x: x.update(pooling_operator="adaptive"),
            lambda x: x.update(pooling_matrix_sha256="0" * 64),
            lambda x: x.update(runner_sha256="0" * 64),
            lambda x: x.update(source_commit="0" * 40),
            lambda x: x.update(manifest_sha256="0" * 64),
            lambda x: x["split"].update(train=[]),
            lambda x: x["environment"].update(deterministic_algorithms=False),
            lambda x: x["arms"].reverse(),
            lambda x: x["arms"][0].update(optimizer_steps=299),
            lambda x: x["arms"][0].update(train_task_ids=[]),
            lambda x: x["arms"][0]["predictions"].pop(),
            lambda x: x["arms"][0]["predictions"][0].update(factor=1.15),
            lambda x: x["arms"][0]["predictions"][0].update(input_sha256="0" * 64),
            lambda x: x["arms"][0]["predictions"][0].update(predicted_layout="B"),
            lambda x: x["arms"][0]["predictions"][0].update(route="reject"),
            lambda x: x["arms"][0]["predictions"][0]["candidate"]["submit"]["point"].update(x=1280),
        ]
        self.assertGreaterEqual(len(changes), 10)
        for change in changes:
            with self.subTest(index=changes.index(change)):
                self.assert_rejected(change)

    def test_aggregate_gain_cannot_hide_a_regressed_perturbed_case(self):
        raw = copy.deepcopy(self.raw)
        cases = [("task-3", "dark_0.85"), ("task-3", "bright_1.15"),
                 ("task-6", "dark_0.85"), ("task-6", "bright_1.15")]
        set_case(raw, self.rows, 0, *cases[0], "A", "accept")
        set_case(raw, self.rows, 0, *cases[1], "B", "yield")
        set_case(raw, self.rows, 0, *cases[2], "A", "yield")
        set_case(raw, self.rows, 0, *cases[3], "A", "yield")
        set_case(raw, self.rows, 1, *cases[0], "B", "yield")
        set_case(raw, self.rows, 1, *cases[1], "A", "accept")
        set_case(raw, self.rows, 1, *cases[2], "B", "accept")
        set_case(raw, self.rows, 1, *cases[3], "A", "yield")
        result = write_and_audit(raw)
        self.assertEqual(result["perturbed_exact"]["no_augmentation"], 1)
        self.assertEqual(result["perturbed_exact"]["brightness_augmentation"], 2)
        self.assertFalse(result["perturbed_exact"]["no_case_regression"])
        self.assertEqual(result["status"], "HOLD_NO_SAFE_BENEFIT")

    def test_accepted_wrong_coordinates_are_fail(self):
        raw = copy.deepcopy(self.raw)
        set_case(raw, self.rows, 1, "task-3", "dark_0.85", "B", "accept")
        result = write_and_audit(raw)
        self.assertEqual(result["status"], "FAIL_ACCEPTED_FALSE_GROUNDING")


if __name__ == "__main__":
    unittest.main(verbosity=2)
