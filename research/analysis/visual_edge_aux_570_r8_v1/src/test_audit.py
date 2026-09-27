#!/usr/bin/env python3
import base64
import json
import tempfile
import unittest
from pathlib import Path

from PIL import Image, ImageChops, ImageFilter, ImageOps

import audit
import build_inputs


class InputTests(unittest.TestCase):
    def test_disjoint_splits_exact_dimensions_and_edge_alignment(self):
        with tempfile.TemporaryDirectory() as td:
            build_inputs.main(td)
            p = Path(td)
            m = json.loads((p / "manifest.json").read_text())
            self.assertEqual(len(m["rows"]), 14)
            self.assertEqual(sum(r["split"] == "construction" for r in m["rows"]), 2)
            self.assertEqual(sum(r["split"] == "formal" for r in m["rows"]), 12)
            self.assertEqual(len({r["seed"] for r in m["rows"]}), 14)
            for r in m["rows"]:
                src = Image.open(p / r["source_file"]).convert("RGB")
                edge = Image.open(p / r["edge_file"]).convert("RGB")
                expected = ImageOps.autocontrast(ImageOps.grayscale(src).filter(ImageFilter.FIND_EDGES)).convert("RGB")
                self.assertEqual(src.size, (1280, 800))
                self.assertIsNone(ImageChops.difference(edge, expected).getbbox())
                self.assertEqual((r["target_box"] is not None), r["present"])
                if r["present"]:
                    x1, y1, x2, y2 = r["target_box"]
                    self.assertTrue(0 <= x1 < x2 < 1280 and 0 <= y1 < y2 < 800)


class AuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.p = Path(cls.tmp.name)
        build_inputs.main(str(cls.p / "inputs"))
        cls.manifest = json.loads((cls.p / "inputs" / "manifest.json").read_text())

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def make_records(self):
        rows = [r for r in self.manifest["rows"] if r["split"] == "construction"]
        records, samples = [], []
        for i, row in enumerate(rows):
            raw = (self.p / "inputs" / row["source_file"]).read_bytes()
            edge = (self.p / "inputs" / row["edge_file"]).read_bytes()
            prompt = row["prompt"]
            arms = ("RAW", "EDGE") if i % 2 == 0 else ("EDGE", "RAW")
            for arm in arms:
                images = [base64.b64encode(raw).decode()]
                if arm == "EDGE": images.append(base64.b64encode(edge).decode())
                req = {"model": "qwen2.5vl:3b", "messages": [{"role": "user", "content": prompt, "images": images}], "options": {"temperature": 0, "seed": row["seed"], "top_p": 1, "top_k": 1, "num_ctx": 8192, "num_predict": 128}, "stream": False, "format": audit.EXPECTED_FORMAT, "keep_alive": "10m"}
                answer = {"present": True, "point": [sum(row["target_box"][::2])//2, sum(row["target_box"][1::2])//2]} if row["present"] else {"present": False, "point": None}
                record = {"case_id": row["case_id"], "split": "construction", "arm": arm, "start_ns": 100+i*20, "end_ns": 110+i*20, "request": req, "request_sha256": audit.sha(audit.canon(req)), "response": {"model": "qwen2.5vl:3b", "message": {"content": json.dumps(answer)}}, "ollama_ps_pre": {"models": [{"name": "qwen2.5vl:3b", "size_vram": 100}]}, "ollama_ps_post": {"models": [{"name": "qwen2.5vl:3b", "size_vram": 100}]}}
                records.append(record)
                samples.append({"timestamp_ns": 105+i*20, "memory_used_mib": 1000})
        return records, samples

    def test_valid_pairs_and_gpu_receipts_pass(self):
        records, samples = self.make_records()
        result = audit.audit(self.manifest, records, "construction", samples, 0)
        self.assertEqual(result["decision"], "CONSTRUCTION_AUDIT_PASS", result["errors"])
        self.assertEqual(result["errors"], [])

    def test_missing_pair_is_rejected(self):
        records, samples = self.make_records()
        result = audit.audit(self.manifest, records[:-1], "construction", samples, 0)
        self.assertIn("call_cardinality_or_identity", result["errors"])

    def test_swapped_edge_bytes_are_rejected(self):
        records, samples = self.make_records()
        target = next(x for x in records if x["arm"] == "EDGE")
        target["request"]["messages"][0]["images"][1] = target["request"]["messages"][0]["images"][0]
        target["request_sha256"] = audit.sha(audit.canon(target["request"]))
        result = audit.audit(self.manifest, records, "construction", samples, 0)
        self.assertTrue(any("edge_image_binding" in e for e in result["errors"]))

    def test_missing_gpu_overlap_is_rejected(self):
        records, _ = self.make_records()
        result = audit.audit(self.manifest, records, "construction", [], 0)
        self.assertTrue(any("gpu_sample_overlap" in e for e in result["errors"]))

    def test_prompt_tampering_is_rejected(self):
        records, samples = self.make_records()
        records[0]["request"]["messages"][0]["content"] += " changed"
        records[0]["request_sha256"] = audit.sha(audit.canon(records[0]["request"]))
        result = audit.audit(self.manifest, records, "construction", samples, 0)
        self.assertTrue(any("prompt_binding" in e for e in result["errors"]))


if __name__ == "__main__":
    unittest.main()
