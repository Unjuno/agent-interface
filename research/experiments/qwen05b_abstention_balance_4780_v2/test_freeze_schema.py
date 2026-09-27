import json
import unittest
import tempfile
from pathlib import Path


class FrozenSchemaTests(unittest.TestCase):
    def test_formal_runner_fields_are_nested_under_declared_sections(self):
        freeze = json.loads((Path(__file__).parent / "FREEZE.json").read_text(encoding="utf-8"))
        self.assertEqual(freeze["issue"], 5014)
        self.assertEqual(freeze["allocation"], "qwen05b-abstention-balance-4780-20260928-02")
        self.assertEqual(freeze["seeds"]["formal_seed"], 73194109)
        self.assertIn('--seed 73194109', freeze['commands']['formal'])
        self.assertNotIn('--seed 73194019', freeze['commands']['formal'])
        self.assertEqual(freeze["data"]["formal_input_sha256"], "cfcf89f19bc4bec7c8bbca80ee9ce4bc77d38dc239c3d6147b77fb7504c42d1d")
        self.assertEqual(freeze["model"]["model_safetensors_sha256"], "fdf756fa7fcbe7404d5c60e26bff1a0c8b8aa1f72ced49e7dd0210fe288fb7fe")
        self.assertEqual(sum(freeze["data"]["support_counts"]["balanced"].values()), 32)
        self.assertEqual(len(freeze["data"]["classes"]), 8)
        self.assertEqual(set(freeze["data"]["training_case_order_sha256"]), {"imbalanced", "balanced"})

    def test_independent_auditor_consumes_nested_schema_without_lookup_error(self):
        from audit_raw import audit
        source = Path(__file__).parent
        freeze = json.loads((source / "FREEZE.json").read_text(encoding="utf-8"))
        data_bytes = Path("/input/formal-dataset.json").read_bytes()
        freeze_sha = (source / "FREEZE.sha256").read_text(encoding="ascii").split()[0]
        orchestration = {"freeze_sha256": freeze_sha, "out_dir": tempfile.mkdtemp(),
                         "model_safetensors_sha256": freeze["model"]["model_safetensors_sha256"],
                         "gpu": "NVIDIA RTX 3080", "formal_seed_fit_invocations": 0,
                         "formal_base_evaluations": 0, "formal_adapter_evaluations": 0}
        raw = {arm: {"schema": "qwen05b-abstention-balance-raw-arm-v1", "arm": arm,
                     "dataset_sha256": freeze["data"]["formal_input_sha256"], "results": []}
               for arm in ("base", "imbalanced", "balanced")}
        report = audit(data_bytes, raw, freeze, orchestration, source)
        errors = report["errors"]
        self.assertNotIn("formal_input_hash", errors)
        self.assertNotIn("input_identity", errors)
        self.assertFalse(any(e.startswith("support_counts:") for e in errors))
        self.assertFalse(any(e.startswith("support_order:") for e in errors))
        self.assertNotIn("model_hash_receipt", errors)
        self.assertIn("base:row_count", errors)
        self.assertEqual(report["disposition"], "STOP_RAW_AUDIT_OR_PROVENANCE")


if __name__ == "__main__":
    unittest.main()