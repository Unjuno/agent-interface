import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import audit as independent


class IndependentAuditMutationTests(unittest.TestCase):
    def run_copy(self, mutate=None):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp)
            for name in ("FREEZE.json", "RUN.json", "STDOUT.bin", "STDERR.bin", "EXECUTION.json"):
                shutil.copyfile(independent.ROOT / name, target / name)
            if mutate:
                raw = json.loads((target / "RUN.json").read_text(encoding="utf-8"))
                mutate(raw)
                (target / "RUN.json").write_text(json.dumps(raw, sort_keys=True, indent=2) + "\n", encoding="utf-8")
            with patch.object(independent, "ROOT", target):
                return independent.audit()

    def test_pristine_retained_raw_passes(self):
        self.assertEqual(self.run_copy()["result"], "PASS")

    def test_missing_case_is_rejected(self):
        result = self.run_copy(lambda raw: raw["cases"].pop())
        self.assertEqual(result["result"], "FAIL")

    def test_forged_candidate_count_is_rejected(self):
        result = self.run_copy(lambda raw: raw.update(candidate_invocations=0))
        self.assertEqual(result["result"], "FAIL")

    def test_invalid_stop_with_raw_hash_is_rejected(self):
        def forge(raw):
            row = next(item for item in raw["cases"] if item["case"] == "candidate_json_truncated")
            row["outcome"]["raw_sha256"] = "a" * 64

        result = self.run_copy(forge)
        self.assertEqual(result["result"], "FAIL")


if __name__ == "__main__":
    unittest.main(verbosity=2)
