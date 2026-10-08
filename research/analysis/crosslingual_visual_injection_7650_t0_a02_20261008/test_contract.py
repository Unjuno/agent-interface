import importlib.util
import json
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent / "crosslingual_visual_injection_7650_t0_a01_20261008"
spec = importlib.util.spec_from_file_location("audit", HERE / "audit.py")
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


class AuditV2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = (ROOT / "RAW.json").read_bytes()
        cls.data = json.loads(cls.raw)
        import hashlib
        cls.digest = hashlib.sha256(cls.raw).hexdigest()

    def test_frozen_predecessor_raw_accepted(self):
        self.assertEqual(self.digest, audit.EXPECTED_RAW_SHA256)
        self.assertEqual(audit.validate(self.data, self.digest), [])

    def test_all_seeded_mutations_rejected(self):
        self.assertTrue(all(audit.mutation_controls(self.data, self.digest).values()))

    def test_aggregate_preserving_swap_changes_no_marginals_but_is_rejected(self):
        rows = self.data["rows"]
        before = sorted(r["task_lang"] for r in rows)
        changed = json.loads(json.dumps(self.data))
        a, b = changed["rows"][0], changed["rows"][12]
        a["task_lang"], b["task_lang"] = b["task_lang"], a["task_lang"]
        self.assertEqual(before, sorted(r["task_lang"] for r in changed["rows"]))
        self.assertIn("uid_task_lang_binding", audit.validate(changed, self.digest))

    def test_raw_hash_mutation_rejected(self):
        self.assertIn("raw_hash_mismatch", audit.validate(self.data, "0" * 64))


if __name__ == "__main__":
    unittest.main()
