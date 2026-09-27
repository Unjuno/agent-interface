import hashlib
import json
import os
import sys
import unittest
from pathlib import Path

import torch
import torch.nn.functional as F


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(REPO / "research/live_control"))

import audit
import generate_corpus
import train_eval
from compiled_form_grounding_v1 import validate


class ConstructionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = HERE
        cls.manifest = json.loads((HERE / "corpus/manifest.json").read_bytes())
        cls.specs = json.loads((HERE / "templates.json").read_bytes())

    def test_source_families_and_every_retained_image_audit(self):
        errors = audit.audit_sources(
            self.manifest, self.specs, HERE / "corpus",
            hashlib.sha256((HERE / "corpus/manifest.json").read_bytes()).hexdigest(),
            self.manifest["generator_sha256"])
        self.assertEqual(errors, [])
        self.assertEqual(len(self.manifest["records"]), 240)
        self.assertEqual(len({row["image_sha256"] for row in self.manifest["records"]}), 240)

    def test_manifest_image_paths_resolve_under_corpus_before_training(self):
        corpus_root = HERE / "corpus"
        resolved = [train_eval.resolve_corpus_image(corpus_root, row)
                    for row in self.manifest["records"]]
        self.assertEqual(len(resolved), 240)
        self.assertTrue(all(path.is_file() for path in resolved))
        for record, path in zip(self.manifest["records"], resolved):
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), record["image_sha256"])
        with self.assertRaisesRegex(ValueError, "escapes corpus"):
            train_eval.resolve_corpus_image(corpus_root, {
                "record_id": "corrupt-path", "image": "../../outside.png"})

    def test_source_auditor_rejects_label_or_split_corruption(self):
        corrupted = json.loads(json.dumps(self.manifest))
        corrupted["records"][0]["field_point"][0] += 8
        errors = audit.audit_sources(
            corrupted, self.specs, HERE / "corpus",
            hashlib.sha256((HERE / "corpus/manifest.json").read_bytes()).hexdigest(),
            self.manifest["generator_sha256"])
        self.assertIn("manifest_sha256_mismatch", errors)
        self.assertTrue(any(error.startswith("field_label_mismatch:") for error in errors))

        corrupted = json.loads(json.dumps(self.manifest))
        corrupted["records"][0]["split"] = "heldout"
        errors = audit.audit_sources(
            corrupted, self.specs, HERE / "corpus",
            hashlib.sha256((HERE / "corpus/manifest.json").read_bytes()).hexdigest(),
            self.manifest["generator_sha256"])
        self.assertTrue(any(error.startswith("record_split_mismatch:") for error in errors))

    def test_renderer_is_deterministic_for_each_split_family(self):
        spec_rows = {row["id"]: row for row in self.specs["families"]}
        manifest_rows = {row["record_id"]: row for row in self.manifest["records"]}
        font = generate_corpus.ImageFont.load_default(size=18)
        for family in ("T01", "T04", "T08", "T09", "T12"):
            for variant in (0, 7, 19):
                image, labels = generate_corpus.render(spec_rows[family], variant, font)
                source = image.resize((1280, 800), generate_corpus.Image.Resampling.NEAREST)
                payload = __import__("io").BytesIO()
                source.save(payload, format="PNG", optimize=False, compress_level=9)
                row = manifest_rows[f"{family}-v{variant:02d}"]
                self.assertEqual(hashlib.sha256(payload.getvalue()).hexdigest(), row["image_sha256"])
                self.assertEqual(labels["field_point"], row["field_point"])
                self.assertEqual(labels["submit_point"], row["submit_point"])

    def test_candidate_contract_and_corruption_controls(self):
        candidate = train_eval.compile_candidate([128, 160, 384, 600])
        self.assertEqual(validate(candidate)["field_point"], [128, 160])
        bad = json.loads(json.dumps(candidate))
        bad["field"]["point"]["x"] = 1280
        with self.assertRaises(ValueError):
            validate(bad)

    def test_independent_prediction_auditor_gate_and_corruption(self):
        predictions = []
        for seed in audit.SEEDS:
            for arm in audit.ARMS:
                for record in self.manifest["records"]:
                    if record["split"] != "heldout":
                        continue
                    gold = record["field_point"] + record["submit_point"]
                    points = list(gold)
                    if arm == "narrow_2_families":
                        points[0] += 8
                    candidate = train_eval.compile_candidate(points)
                    validated = validate(candidate)
                    predictions.append({"seed": seed, "arm": arm, "family_id": record["family_id"],
                                        "record_id": record["record_id"], "image_sha256": record["image_sha256"],
                                        "predicted_points": points, "gold_points": gold,
                                        "candidate": candidate,
                                        "validator_points": validated["field_point"] + validated["submit_point"],
                                        "validator": "accept", "validator_error": None,
                                        "exact_coordinates": points == gold})
        model_runs = []
        for seed in audit.SEEDS:
            for arm, families in (("narrow_2_families", ["T01", "T02"]),
                                  ("broad_8_families", list(train_eval.BROAD_FAMILIES))):
                model_runs.append({"seed": seed, "arm": arm, "training_families": families,
                                   "unique_training_images": 20 * len(families),
                                   "optimizer_steps": 500, "sampled_examples": 8000,
                                   "train_seconds": 1.0, "first_sampled_batch_loss": 0.5,
                                   "last_sampled_batch_loss": 0.1,
                                   "peak_cuda_allocated_bytes": 123456})
        result = {"formal_invocations": 1, "retries": 0, "models": 6,
                  "training_steps_per_model": 500, "model_runs": model_runs,
                  "predictions": predictions}
        report = audit.audit_predictions(result, self.manifest, validate)
        self.assertEqual(report["audit_status"], "PASS")
        self.assertEqual(report["disposition"], "PASS_TEMPLATE_DIVERSITY_BENEFIT")
        corrupted = json.loads(json.dumps(result))
        corrupted["predictions"][0]["candidate"]["field"]["point"]["x"] += 8
        bad_report = audit.audit_predictions(corrupted, self.manifest, validate)
        self.assertEqual(bad_report["audit_status"], "FAIL")
        self.assertTrue(any(error.startswith("candidate_prediction_mismatch:")
                            for error in bad_report["integrity_errors"]))
        bad = json.loads(json.dumps(candidate))
        bad["method"]["second_action"] = "click_anywhere"
        with self.assertRaises(ValueError):
            validate(bad)
        bad = json.loads(json.dumps(candidate))
        bad["submit"]["point"] = dict(bad["field"]["point"])
        with self.assertRaises(ValueError):
            validate(bad)

    def test_full_cpu_model_shape_and_pool_oracle(self):
        torch.manual_seed(4546)
        model = train_eval.TinyGrounder().eval()
        images = torch.randn((4, 1, 100, 160), dtype=torch.float32)
        with torch.no_grad():
            feature_map = model.features[:6](images)
            self.assertEqual(tuple(feature_map.shape), (4, 16, 25, 40))
            pooled = model.features[6](feature_map)
            oracle = F.adaptive_avg_pool2d(feature_map, (8, 10))
            self.assertLessEqual(float((pooled - oracle).abs().max()), 1e-6)
            output = model(images)
        self.assertEqual(tuple(output.shape), (4, 4))
        self.assertTrue(bool(((output >= 0) & (output <= 1)).all()))


@unittest.skipUnless(torch.cuda.is_available(), "local CUDA device required")
class CudaConstructionTests(unittest.TestCase):
    def test_repeated_cuda_forward_backward_is_deterministic(self):
        self.assertEqual(os.environ.get("CUBLAS_WORKSPACE_CONFIG"), ":4096:8")
        torch.backends.cuda.matmul.allow_tf32 = False
        torch.backends.cudnn.allow_tf32 = False
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False
        torch.use_deterministic_algorithms(True)
        torch.manual_seed(4546)
        model = train_eval.TinyGrounder().cuda().eval()
        data = torch.randn((4, 1, 100, 160), device="cuda")

        def one_pass():
            x = data.detach().clone().requires_grad_(True)
            output = model(x)
            output.square().sum().backward()
            return output.detach(), x.grad.detach()

        y1, g1 = one_pass()
        y2, g2 = one_pass()
        torch.cuda.synchronize()
        self.assertTrue(torch.equal(y1, y2))
        self.assertTrue(torch.equal(g1, g2))
        self.assertTrue(torch.are_deterministic_algorithms_enabled())
        self.assertEqual(tuple(y1.shape), (4, 4))


if __name__ == "__main__":
    unittest.main(verbosity=2)
