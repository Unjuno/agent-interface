"""Mutation and receipt-boundary tests against construction packages."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, "/src")
import support_loader


class PackageControls(unittest.TestCase):
    def test_one_byte_digest_tamper_and_duplicate_key_reject(self):
        root = Path(__file__).parent / "construction-output"
        for arm in ("control16", "treatment64"):
            d = root / arm
            original = (d / "skill.json").read_bytes()
            expected = json.loads((d / "expected.json").read_text(encoding="utf-8"))
            obj = json.loads(original)
            obj["payload_sha256"] = ("0" if obj["payload_sha256"][0] != "0" else "1") + obj["payload_sha256"][1:]
            tampered = support_loader.canonical(obj)
            self.assertEqual(sum(a != b for a, b in zip(original, tampered)), 1)
            with tempfile.NamedTemporaryFile() as f:
                f.write(tampered); f.flush()
                with self.assertRaises(ValueError):
                    support_loader.validate(f.name, expected)
            raw = original.decode("utf-8").replace('"schema":"unjuno.role-skill.numeric-json.v1"',
                   '"schema":"unjuno.role-skill.numeric-json.v1","schema":"duplicate"', 1)
            with tempfile.NamedTemporaryFile(mode="w+", encoding="utf-8") as f:
                f.write(raw); f.flush()
                with self.assertRaisesRegex(ValueError, "duplicate_key"):
                    support_loader.validate(f.name, expected)

    def test_stale_receipts_and_invalid_edges_do_not_emit(self):
        graph = support_loader.Graph(7865001)
        start = graph.state()
        for args in (("A", "C", 7865001, "skip", "A-v1", True, "synthetic-fixture-v1"),
                     ("A", "B", 7865000, "stale", "A-v1", True, "synthetic-fixture-v1"),
                     ("A", "B", 7865001, "unverified", "A-v1", False, "synthetic-fixture-v1")):
            self.assertEqual(graph.step(*args), "YIELD")
            self.assertEqual(graph.state(), start)
        self.assertEqual(graph.emissions, 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
