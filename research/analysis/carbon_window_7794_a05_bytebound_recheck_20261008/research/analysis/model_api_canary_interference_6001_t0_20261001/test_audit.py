import json
import tempfile
import unittest
from pathlib import Path

from audit import audit


class AuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = Path("raw.jsonl").read_text(encoding="utf-8").splitlines()

    def run_rows(self, lines):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "raw.jsonl"
            path.write_text("\n".join(lines) + "\n", encoding="utf-8")
            return audit(str(path))

    def test_frozen_raw_passes(self):
        result = self.run_rows(self.source)
        self.assertEqual(result["verdict"], "PASS_METHOD_SCOPED")
        self.assertEqual(result["n_rows"], 3840)

    def test_duplicate_attempt_is_rejected(self):
        result = self.run_rows(self.source + [self.source[0]])
        self.assertEqual(result["verdict"], "FAIL_AUDIT")
        self.assertTrue(any("duplicate" in e for e in result["errors"]))

    def test_route_reordering_is_rejected(self):
        row = json.loads(self.source[0])
        row["events"] = list(reversed(row["events"]))
        result = self.run_rows([json.dumps(row)] + self.source[1:])
        self.assertEqual(result["verdict"], "FAIL_AUDIT")
        self.assertTrue(any("route order" in e for e in result["errors"]))

    def test_planted_shift_provenance_tamper_is_rejected(self):
        row = json.loads(self.source[3 * 4 * 240])
        row["semantic_shift_planted"] = not row["semantic_shift_planted"]
        lines = self.source.copy()
        lines[3 * 4 * 240] = json.dumps(row)
        result = self.run_rows(lines)
        self.assertEqual(result["verdict"], "FAIL_AUDIT")
        self.assertTrue(any("provenance" in e for e in result["errors"]))


if __name__ == "__main__":
    unittest.main(verbosity=2)
