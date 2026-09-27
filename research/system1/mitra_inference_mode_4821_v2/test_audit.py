import copy
import unittest

from audit import audit


def fixture():
    rows = []
    for i in range(16):
        for j in range(4):
            for arm in ("A", "B"):
                p = [0.2, 0.2, 0.2, 0.2, 0.1, 0.1]
                if arm == "A":
                    p[0] += j * 1e-4
                    p[1] -= j * 1e-4
                modules = [{"name": "", "type": "Model", "training": arm == "A"},
                           {"name": "drop", "type": "Dropout", "training": arm == "A"}]
                rows.append({"row_index": i, "repeat_index": j, "arm": arm, "probabilities": p,
                             "order": ["A", "B"] if i % 2 == 0 else ["B", "A"],
                             "modules_before": modules, "modules_after": modules})
    return {"schema": "mitra-inference-mode-diagnostic-4947-v2", "allocation": "mitra-inference-mode-diagnostic-4821-v2-20260928-01", "issue": 4947,
            "runtime": {"optimizer_step_calls": 0, "model_load_seconds": [0.1],
                        "model_sha256": "model-sha", "support_sha256": "support-sha", "queries_sha256": "queries-sha"},
            "main_intake_sha": "main-sha", "image_id": "image-id",
            "freeze_sha256": "freeze-sha",
            "expected_input_sha256": {"support": "support-sha", "queries": "queries-sha"},
            "source_sha256": {"probe.py": "source-sha"},
            "natural_module_state": [{"name": "", "type": "Model", "training": True},
                                     {"name": "drop", "type": "Dropout", "training": True}],
            "natural_active_dropout_modules": ["drop"],
            "predictions": rows}


class AuditTests(unittest.TestCase):
    def test_runner_uses_model_directory_not_weight_file_as_repo_id(self):
        from pathlib import Path
        source = Path(__file__).with_name("probe.py").read_text(encoding="utf-8")
        self.assertIn("hf_model=str(base.MODEL)", source)
        self.assertNotIn("hf_model=str(model_path)", source)

    def freeze(self):
        return {"allocation": "mitra-inference-mode-diagnostic-4821-v2-20260928-01", "main_intake_sha": "main-sha", "execution": {"image_id": "image-id"},
                "inputs": {"support": {"sha256": "support-sha"}, "queries": {"sha256": "queries-sha"}},
                "model": {"sha256": "model-sha"}, "source_sha256": {"probe.py": "source-sha"}}

    def test_valid_raw_passes_audit_and_gate(self):
        result = audit(fixture(), self.freeze(), "freeze-sha")
        self.assertEqual([], result["errors"])
        self.assertEqual("PASS_EVAL_MODE_EXPLAINS_REPEAT_DRIFT_SCOPED", result["scientific_disposition"])

    def test_duplicate_row_is_rejected(self):
        raw = fixture()
        raw["predictions"][-1] = copy.deepcopy(raw["predictions"][0])
        self.assertIn("POPULATION_OR_DUPLICATES", audit(raw)["errors"])

    def test_probability_mutation_is_rejected(self):
        raw = fixture()
        raw["predictions"][0]["probabilities"][0] = float("nan")
        self.assertIn("PROBABILITY_VECTOR", audit(raw)["errors"])

    def test_active_dropout_in_eval_arm_is_rejected(self):
        raw = fixture()
        row = next(x for x in raw["predictions"] if x["arm"] == "B")
        row["modules_before"][1]["training"] = True
        self.assertIn("EVAL_ARM_ACTIVE_DROPOUT", audit(raw)["errors"])

    def test_source_identity_mutation_is_rejected(self):
        raw = fixture()
        raw["source_sha256"]["probe.py"] = "changed"
        self.assertIn("SOURCE_IDENTITY", audit(raw, self.freeze(), "freeze-sha")["errors"])

    def test_freeze_hash_mutation_is_rejected(self):
        raw = fixture()
        raw["freeze_sha256"] = "changed"
        self.assertIn("FREEZE_HASH", audit(raw, self.freeze(), "freeze-sha")["errors"])


if __name__ == "__main__":
    unittest.main()

