import json
import tempfile
import unittest
from pathlib import Path

import auditor
import candidate


class ProtocolTests(unittest.TestCase):
    def fixture(self, d):
        p = Path(d) / "candidate.json"
        candidate.main(p)
        return p, json.loads(p.read_text())

    def test_exact_denominator_and_independent_audit(self):
        with tempfile.TemporaryDirectory() as d:
            p, _ = self.fixture(d)
            result = auditor.audit(p)
            self.assertEqual(result["status"], "PASS_METHOD_SCOPED")
            self.assertEqual(result["rows_seen"], 12)

    def test_zero_lifetime_has_stepwise_histories(self):
        with tempfile.TemporaryDirectory() as d:
            p, data = self.fixture(d)
            rows = data["rows"]
            zero = [r for r in rows if r["lifetime"] == "ZERO"]
            self.assertTrue(all(len(r["histories"]) == 8 for r in zero))
            event = [r for r in rows if r["lifetime"] == "EVENT"]
            self.assertTrue(all(len(r["histories"]) == 4 for r in event))
            self.assertEqual(event[0]["histories"], [[0,0,0],[0,1,1],[1,0,0],[1,1,1]])

    def test_missing_receipt_does_not_narrow(self):
        with tempfile.TemporaryDirectory() as d:
            p, data = self.fixture(d)
            rows = data["rows"]
            for life in ("FULL", "ZERO", "EVENT"):
                pair = [r for r in rows if r["lifetime"] == life and r["order"] == "AGENT_FIRST"]
                self.assertEqual(pair[0]["histories"], pair[1]["histories"])

    def test_auditor_rejects_silent_zero_to_full_collapse(self):
        with tempfile.TemporaryDirectory() as d:
            p, data = self.fixture(d)
            # Frozen corruption controls: changed partial event boundary,
            # zero-to-full collapse, missing-receipt narrowing, leaked move
            # order, missing row, and an unsafe admitted successor.
            corruptions = []
            changed = json.loads(json.dumps(data))
            changed["rows"][8]["histories"] = [[0,0,0],[1,1,1]]; corruptions.append(changed)
            changed = json.loads(json.dumps(data)); changed["rows"][4]["histories"] = [[0,0,0],[1,1,1]]; corruptions.append(changed)
            changed = json.loads(json.dumps(data)); changed["rows"][1]["histories"] = [[0,0,0]]; corruptions.append(changed)
            changed = json.loads(json.dumps(data)); changed["rows"][0]["nature_information"] = "action+public-observation"; corruptions.append(changed)
            changed = json.loads(json.dumps(data)); changed["rows"][2]["nature_information"] = "public-observation"; corruptions.append(changed)
            changed = json.loads(json.dumps(data)); changed["rows"].pop(); corruptions.append(changed)
            changed = json.loads(json.dumps(data)); changed["rows"][0]["unsafe_admission"] = True; corruptions.append(changed)
            for index, corrupted in enumerate(corruptions):
                p.write_text(json.dumps(corrupted))
                with self.subTest(corruption=index):
                    self.assertEqual(auditor.audit(p)["status"], "FAIL_METHOD")

    def test_auditor_rejects_nature_information_leak(self):
        with tempfile.TemporaryDirectory() as d:
            p, data = self.fixture(d)
            data["rows"][0]["nature_information"] = "action+public-observation"
            p.write_text(json.dumps(data))
            self.assertEqual(auditor.audit(p)["status"], "FAIL_METHOD")


if __name__ == "__main__":
    unittest.main()
