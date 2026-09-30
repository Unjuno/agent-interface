from __future__ import annotations

import base64
import json
import tempfile
import unittest
from pathlib import Path

from audit import audit, iou


class AuditTests(unittest.TestCase):
    def make_fixture(self, root: Path) -> None:
        (root / "data").mkdir()
        (root / "formal").mkdir()
        prompt = "frozen prompt"
        cases = []
        samples = []
        for i in range(8):
            positive = i < 6
            name = f"positive-{i+1:02d}" if positive else f"absent-{i-5:02d}"
            img = f"synthetic-{name}".encode()
            (root / "data" / f"{name}.png").write_bytes(img)
            target = [10, 10, 20, 20] if positive else None
            case = {"case_id": name, "seed": 100+i, "present": positive, "target_box": target,
                    "image_path": f"{name}.png", "image_sha256": __import__("hashlib").sha256(img).hexdigest()}
            cases.append(case)
            response = {"present": positive, "box": target}
            request = {"model": "qwen2.5vl:3b", "messages": [{"role": "user", "content": prompt,
                        "images": [base64.b64encode(img).decode()]}], "stream": False,
                       "options": {"temperature": 0, "seed": 100+i, "num_predict": 128}}
            rec = {"model": "qwen2.5vl:3b", "expected_digest": "fb90415cde1ef08aa669ae74b082d49b158729b6db1ab183c941417d507e71a1",
                   "request": request, "image_sha256": case["image_sha256"], "prompt_sha256": "not-scored",
                   "started_utc_ns": i*100, "ended_utc_ns": i*100+50,
                   "response": {"message": {"content": json.dumps(response)}}}
            (root / "formal" / f"{name}.json").write_text(json.dumps(rec), encoding="utf-8")
            samples.append({"utc_ns": i*100+25, "memory_used_mib": 500, "ollama_ps_stdout": "qwen 100% GPU"})
        (root / "data" / "PREFORMAL.json").write_text(json.dumps({"prompt": prompt, "formal_cases": cases}), encoding="utf-8")
        (root / "baseline.json").write_text(json.dumps({"memory_used_mib": 100}), encoding="utf-8")
        (root / "sampler.jsonl").write_text("\n".join(json.dumps(row) for row in samples), encoding="utf-8")

    def test_iou_exact_and_disjoint(self):
        self.assertEqual(iou([1, 2, 11, 12], [1, 2, 11, 12]), 1.0)
        self.assertEqual(iou([1, 2, 3, 4], [5, 6, 7, 8]), 0.0)

    def test_complete_gpu_localization_block_passes(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.make_fixture(root)
            self.assertEqual(audit(root)["decision"], "PASS_DIAGNOSTIC_SCOPED")

    def test_missing_gpu_overlap_is_hold(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.make_fixture(root)
            rows = [json.loads(x) for x in (root / "sampler.jsonl").read_text().splitlines()]
            for row in rows:
                row["memory_used_mib"] = 100
                row["ollama_ps_stdout"] = "qwen 100% CPU"
            (root / "sampler.jsonl").write_text("\n".join(json.dumps(x) for x in rows))
            self.assertEqual(audit(root)["decision"], "HOLD_AUDIT_OR_GPU_GATE")

    def test_mutated_request_image_is_detected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.make_fixture(root)
            path = root / "formal" / "positive-01.json"
            rec = json.loads(path.read_text())
            rec["request"]["messages"][0]["images"][0] = base64.b64encode(b"different").decode()
            path.write_text(json.dumps(rec))
            self.assertIn("request_image:positive-01", audit(root)["errors"])


if __name__ == "__main__":
    unittest.main(verbosity=2)

