import copy
import json
import shutil
import tempfile
import unittest

from analyze import analyze
from analyze_v2 import analyze as analyze_v2
from verify_v2 import canonical, verify
from pathlib import Path


HERE = Path(__file__).resolve().parent


class AuditV2Tests(unittest.TestCase):
    def test_retained_package_verifies(self):
        result = verify(HERE)
        self.assertEqual(result["status"], "PASS_RETAINED_MANUAL_GUARDED_DIRECT_SIX_PAIR_AUDIT_V2")
        self.assertEqual(result["integration_gate"], "HOLD_INTEGRATION_INCOMPLETE")

    def test_deterministic_analysis_and_refusal_permutation(self):
        root = HERE / "_v2_fixture"
        try:
            import tempfile, tarfile
            with tempfile.TemporaryDirectory() as td:
                with tarfile.open(HERE / "raw.tar.gz", "r:gz") as archive:
                    archive.extractall(td, filter="data")
                root = Path(td) / "post-release-spine-02"
                result = analyze_v2(root)
                direct = analyze(root)
                self.assertEqual(canonical(result), canonical(direct))
                refusal = result["routes"]["guarded-local"]["refusals"]
                shuffled = copy.deepcopy(result)
                shuffled["routes"]["guarded-local"]["refusals"] = list(reversed(refusal))
                self.assertEqual(canonical(shuffled), canonical(result))
        finally:
            pass

    def test_duplicate_attempt_rejected(self):
        value = {"routes": {"x": {"refusals": [{"attempt": 1}, {"attempt": 1}]}}}
        with self.assertRaisesRegex(ValueError, "duplicate refusal attempt"):
            canonical(value)

    def test_refusal_content_and_other_order_stay_strict(self):
        base = {"routes": {"x": {"refusals": [{"attempt": 1, "detail": "a"}],
                                   "rows": [1, 2]}}}
        changed = copy.deepcopy(base)
        changed["routes"]["x"]["refusals"][0]["detail"] = "b"
        reordered = copy.deepcopy(base)
        reordered["routes"]["x"]["rows"] = [2, 1]
        self.assertNotEqual(canonical(base), canonical(changed))
        self.assertNotEqual(canonical(base), canonical(reordered))

    def _temporary_published_package(self):
        temp = tempfile.TemporaryDirectory()
        dest = Path(temp.name)
        for name in ("manifest.json", "raw.tar.gz", "analysis.json", "model-usage-projection.json"):
            shutil.copy2(HERE / name, dest / name)
        return temp, dest

    def test_full_verifier_accepts_only_refusal_inventory_permutation(self):
        temp, dest = self._temporary_published_package()
        try:
            analysis_path = dest / "analysis.json"
            published = json.loads(analysis_path.read_text())
            published["routes"]["guarded-local"]["refusals"].reverse()
            analysis_path.write_text(json.dumps(published))
            self.assertEqual(verify(dest)["integration_gate"], "HOLD_INTEGRATION_INCOMPLETE")
        finally:
            temp.cleanup()

    def test_full_verifier_rejects_changed_refusal_content(self):
        temp, dest = self._temporary_published_package()
        try:
            analysis_path = dest / "analysis.json"
            published = json.loads(analysis_path.read_text())
            published["routes"]["guarded-local"]["refusals"][0]["detail"] += " altered"
            analysis_path.write_text(json.dumps(published))
            with self.assertRaisesRegex(ValueError, "analysis mismatch"):
                verify(dest)
        finally:
            temp.cleanup()

    def test_full_verifier_rejects_other_list_reordering(self):
        temp, dest = self._temporary_published_package()
        try:
            analysis_path = dest / "analysis.json"
            published = json.loads(analysis_path.read_text())
            rows = published["routes"]["guarded-local"]["rows"]
            rows[0], rows[1] = rows[1], rows[0]
            analysis_path.write_text(json.dumps(published))
            with self.assertRaisesRegex(ValueError, "analysis mismatch"):
                verify(dest)
        finally:
            temp.cleanup()


if __name__ == "__main__":
    unittest.main()
