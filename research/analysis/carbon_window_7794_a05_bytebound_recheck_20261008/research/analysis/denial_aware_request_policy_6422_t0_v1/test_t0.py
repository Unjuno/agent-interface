import json
import tempfile
import unittest
from pathlib import Path
import candidate
import auditor

HERE = Path(__file__).resolve().parent


class T0(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = json.loads((HERE / "fixture.json").read_text())
        cls.rows = candidate.run(cls.fixture)

    def test_coverage_and_oracle(self):
        self.assertEqual(len(self.rows), 60)
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "raw.jsonl"
            p.write_text("".join(json.dumps(r) + "\n" for r in self.rows))
            self.assertEqual(auditor.audit(p)["status"], "PASS_METHOD_SCOPED")

    def test_rejects_all_frozen_corruptions(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "raw.jsonl"
            p.write_text("".join(json.dumps(r) + "\n" for r in self.rows))
            for mutation in ("erased_denial", "forged_reopen", "principal_mapping", "hidden_effect"):
                with self.subTest(mutation=mutation):
                    self.assertEqual(auditor.audit(p, mutation)["status"], "FAIL_AUDIT")


if __name__ == "__main__": unittest.main()
