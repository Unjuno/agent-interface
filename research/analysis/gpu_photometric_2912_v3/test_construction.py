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

import train_eval as runner
import audit
from compiled_form_grounding_v1 import validate


class ConstructionTests(unittest.TestCase):
    def test_manifest_and_all_six_image_bytes_match_pins(self):
        manifest_path = REPO / "research/analysis/local_model_2912_image_manifest.json"
        manifest_bytes = manifest_path.read_bytes().replace(b"\r\n", b"\n")
        self.assertEqual(hashlib.sha256(manifest_bytes).hexdigest(), runner.EXPECTED_MANIFEST_SHA256)
        manifest = json.loads(manifest_bytes)
        rows = {row["task_id"]: row for row in manifest["records"]}
        self.assertEqual(set(rows), set(runner.EXPECTED_IMAGES))
        for task, expected in runner.EXPECTED_IMAGES.items():
            image = (REPO / rows[task]["image"]).read_bytes()
            self.assertEqual(hashlib.sha256(image).hexdigest(), expected, task)
            self.assertEqual(rows[task]["image_sha256"], expected, task)

    def test_fixed_matrices_match_adaptive_pool_cpu_oracle(self):
        torch.manual_seed(4470)
        x = torch.randn((2, 16, 40, 25), dtype=torch.float32)
        actual = runner.DeterministicAdaptiveAvgPool2d()(x)
        expected = F.adaptive_avg_pool2d(x, (8, 10))
        self.assertEqual(tuple(actual.shape), (2, 16, 8, 10))
        self.assertLessEqual(float((actual - expected).abs().max()), 1e-6)
        self.assertEqual(runner.pooling_matrix_sha256(), audit.expected_pooling_matrix_sha256())

    def test_compiled_candidates_pass_and_mutated_bounds_fail(self):
        manifest = json.loads((REPO / "research/analysis/local_model_2912_image_manifest.json").read_text())
        rows = {row["task_id"]: row for row in manifest["records"]}
        points = {row["layout"]: (row["field_point"], row["submit_point"])
                  for row in rows.values()}
        for layout in ("A", "B"):
            self.assertIn(validate(runner.compile_candidate(layout, points))["field_point"],
                          [points[layout][0]])
        bad = runner.compile_candidate("A", points)
        bad["submit"]["point"]["x"] = 1280
        with self.assertRaises(ValueError):
            validate(bad)


@unittest.skipUnless(torch.cuda.is_available(), "local CUDA device required for deterministic construction gate")
class CudaConstructionTests(unittest.TestCase):
    def test_repeated_cuda_forward_backward_is_deterministic(self):
        self.assertEqual(os.environ.get("CUBLAS_WORKSPACE_CONFIG"), ":4096:8")
        torch.backends.cuda.matmul.allow_tf32 = False
        torch.backends.cudnn.allow_tf32 = False
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False
        torch.use_deterministic_algorithms(True)
        torch.manual_seed(4470)
        source = torch.randn((16, 16, 40, 25), dtype=torch.float32)
        oracle = F.adaptive_avg_pool2d(source, (8, 10))
        pool = runner.DeterministicAdaptiveAvgPool2d().cuda()
        weight = torch.arange(16 * 16 * 8 * 10, device="cuda", dtype=torch.float32)
        weight = weight.reshape((16, 16, 8, 10)).remainder(17).div_(17)

        def forward_backward():
            x = source.cuda().detach().clone().requires_grad_(True)
            y = pool(x)
            (y * weight).sum().backward()
            return y.detach(), x.grad.detach()

        y1, g1 = forward_backward()
        y2, g2 = forward_backward()
        torch.cuda.synchronize()
        self.assertEqual(tuple(y1.shape), (16, 16, 8, 10))
        self.assertLessEqual(float((y1.cpu() - oracle).abs().max()), 1e-6)
        self.assertTrue(torch.equal(y1, y2))
        self.assertTrue(torch.equal(g1, g2))
        self.assertTrue(torch.are_deterministic_algorithms_enabled())
        self.assertFalse(torch.backends.cuda.matmul.allow_tf32)


if __name__ == "__main__":
    unittest.main(verbosity=2)
