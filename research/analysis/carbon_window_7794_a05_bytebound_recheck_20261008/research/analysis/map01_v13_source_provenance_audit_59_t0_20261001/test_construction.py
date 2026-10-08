import hashlib
import json
import unittest
from unittest.mock import patch

import auditor


class SourceClosureAuditTests(unittest.TestCase):
    def setUp(self):
        self.fixture = {
            "source_commit": "frozen-main",
            "prereg_path": "prereg.json",
            "historical_allocation_id": "old-allocation",
        }
        self.files = {"src/a.py": b"alpha\n", "src/b.py": b"bravo\n"}
        self.prereg = {
            "allocation_id": "old-allocation",
            "base_commit": "old-base",
            "source_sha256": {"src/a.py": hashlib.sha256(self.files["src/a.py"]).hexdigest()},
            "canonical_upstream_sha256": {"src/b.py": hashlib.sha256(self.files["src/b.py"]).hexdigest()},
        }
        self.prereg_bytes = json.dumps(self.prereg).encode()
    def run_audit(self, changed_files=None, candidate=None):
        changed_files = self.files if changed_files is None else changed_files

        pins = {}
        for key in ("source_sha256", "canonical_upstream_sha256"):
            for path, digest in self.prereg[key].items():
                pins.setdefault(path, set()).add(digest)
        rows = []
        for path in sorted(pins):
            raw = changed_files.get(path)
            rows.append({
                "path": path,
                "expected_sha256": sorted(pins[path]),
                "actual_sha256": hashlib.sha256(raw).hexdigest() if raw is not None else None,
                "present": raw is not None,
            })
        fresh_candidate = {
            "source_commit": "frozen-main", "prereg_path": "prereg.json",
            "expected_source_path_count": len(pins), "rows": rows,
        }

        def fake_show(_root, _commit, path):
            if path == "prereg.json":
                return self.prereg_bytes
            return changed_files.get(path)

        with patch.object(auditor, "show", side_effect=fake_show):
            return auditor.audit(None, self.fixture, fresh_candidate if candidate is None else candidate)

    def test_complete_exact_source_union_passes_source_layer(self):
        result = self.run_audit()
        self.assertEqual("PASS_SOURCE_CLOSURE_ONLY", result["disposition"])
        self.assertEqual(2, result["independently_verified_path_count"])
        self.assertFalse(result["live_validation_authorized"])

    def test_pinned_content_drift_is_not_relabelled_pass(self):
        result = self.run_audit(changed_files={"src/a.py": b"changed\n", "src/b.py": b"bravo\n"})
        self.assertEqual("FAIL_PINNED_SOURCE_DRIFT", result["disposition"])
        self.assertEqual(["src/a.py"], result["drift_paths"])

    def test_missing_candidate_row_fails_audit_integrity(self):
        raw = self.files["src/a.py"]
        candidate = {
            "source_commit": "frozen-main",
            "prereg_path": "prereg.json",
            "expected_source_path_count": 2,
            "rows": [{
                "path": "src/a.py",
                "expected_sha256": [hashlib.sha256(raw).hexdigest()],
                "actual_sha256": hashlib.sha256(raw).hexdigest(),
                "present": True,
            }],
        }
        result = self.run_audit(candidate=candidate)
        self.assertEqual("FAIL_AUDIT_INTEGRITY", result["disposition"])
        self.assertIn("candidate-inventory-not-exact-union", result["errors"])

    def test_conflicting_duplicate_pins_fail_closed(self):
        self.prereg["canonical_upstream_sha256"]["src/a.py"] = "0" * 64
        self.prereg_bytes = json.dumps(self.prereg).encode()
        result = self.run_audit()
        self.assertEqual("FAIL_PINNED_SOURCE_DRIFT", result["disposition"])
        self.assertEqual(["src/a.py"], result["drift_paths"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
