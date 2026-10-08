import hashlib
import json
import unittest

import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image

from adapter import candidate, cell_to_point
from freeze_corpus import make_manifest
from model import DeterministicAdaptiveAvgPool2d, TinyCoordinateGrounder, loss_for
from render import FAMILIES, RENDERER_ID, render, source_family_sha256, source_point


class FixedPoolConstructionTests(unittest.TestCase):
    def test_prefrozen_corpus_image_and_label_hashes(self):
        with open("corpus_manifest.json", encoding="utf-8") as f:
            frozen = json.load(f)
        self.assertEqual(make_manifest(), frozen)
        self.assertEqual(len(frozen["images"]), 48)
        self.assertEqual(len({row["png_sha256"] for row in frozen["images"]}), 48)

    def test_fixed_pool_matches_adaptive_average_oracle(self):
        torch.manual_seed(56101)
        x = torch.randn(16, 16, 25, 40)
        actual = DeterministicAdaptiveAvgPool2d()(x)
        expected = F.adaptive_avg_pool2d(x, (8, 10))
        self.assertEqual(tuple(actual.shape), (16, 16, 8, 10))
        self.assertLessEqual(float((actual - expected).abs().max()), 1e-6)

    def test_full_model_shape_loss_and_backpropagate(self):
        torch.manual_seed(56102)
        model = TinyCoordinateGrounder()
        x = torch.rand(4, 1, 100, 160)
        labels = [{"field_cell": [i % 8, i % 10], "submit_cell": [(i + 2) % 8, (i + 4) % 10]}
                  for i in range(4)]
        logits = model(x)
        self.assertEqual(tuple(logits.shape), (4, 2, 8, 10))
        loss = loss_for(logits, labels)
        loss.backward()
        self.assertTrue(torch.isfinite(loss).item())
        self.assertGreater(sum(p.grad is not None for p in model.parameters()), 0)

    def test_deterministic_renderer_family_split_and_pixel_labels(self):
        self.assertEqual(len(FAMILIES), 12)
        ids = [s["id"] for s in FAMILIES]
        self.assertEqual(len(set(ids)), 12)
        self.assertEqual(len({source_family_sha256(s) for s in FAMILIES}), 12)
        train, heldout = FAMILIES[:8], FAMILIES[8:]
        self.assertFalse({source_family_sha256(s) for s in train} &
                         {source_family_sha256(s) for s in heldout})
        for spec in FAMILIES:
            for variant in range(4):
                image1, label1 = render(spec, variant)
                image2, label2 = render(spec, variant)
                self.assertEqual(image1.size, (160, 100))
                self.assertEqual(label1, label2)
                self.assertEqual(hashlib.sha256(image1.tobytes()).digest(),
                                 hashlib.sha256(image2.tobytes()).digest())
                self.assertEqual(label1["field_point"], source_point(spec["field"]))
                self.assertEqual(label1["submit_point"], source_point(spec["submit"]))
                self.assertNotEqual(label1["field_point"], label1["submit_point"])

    def test_adapter_strict_validator_and_corruption_rejection(self):
        spec = FAMILIES[0]
        value, parsed = candidate(spec["field"], spec["submit"])
        self.assertEqual(parsed["field_point"], source_point(spec["field"]))
        self.assertEqual(parsed["submit_point"], source_point(spec["submit"]))
        bad = {**value, "extra": True}
        with self.assertRaises(ValueError):
            from compiled_form_grounding_v1 import validate
            validate(bad)
        logits = torch.zeros(2, 8, 10)
        logits[0, spec["field"][0], spec["field"][1]] = 10
        logits[1, spec["submit"][0], spec["submit"][1]] = 10
        cells, confidence = cell_to_point(logits)
        self.assertEqual(cells, [spec["field"], spec["submit"]])
        self.assertTrue(all(c > 0.75 for c in confidence))

    @unittest.skipUnless(torch.cuda.is_available(), "local CUDA GPU unavailable")
    def test_deterministic_cuda_full_forward_backward(self):
        torch.use_deterministic_algorithms(True)
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False
        torch.backends.cuda.matmul.allow_tf32 = False
        torch.backends.cudnn.allow_tf32 = False
        torch.manual_seed(56103)
        model = TinyCoordinateGrounder().cuda()
        x = torch.randn(16, 1, 100, 160, device="cuda", requires_grad=True)
        first = model(x)
        first.sum().backward()
        grad1 = x.grad.detach().clone()
        output1 = first.detach().clone()
        model.zero_grad(set_to_none=True)
        x.grad = None
        second = model(x)
        second.sum().backward()
        self.assertTrue(torch.equal(output1, second.detach()))
        self.assertTrue(torch.equal(grad1, x.grad))


if __name__ == "__main__":
    unittest.main()
