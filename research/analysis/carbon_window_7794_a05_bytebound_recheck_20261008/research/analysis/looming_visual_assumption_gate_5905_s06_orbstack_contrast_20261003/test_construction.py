from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

import audit
import build_fixture
import candidate


class ConstructionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        old = build_fixture.ROOT
        build_fixture.ROOT = self.root
        build_fixture.main()
        build_fixture.ROOT = old

    def tearDown(self):
        self.tmp.cleanup()

    def test_fixture_has_12_rows_and_opaque_candidate_fields(self):
        truth = json.loads((self.root / "truth.json").read_text())
        public = json.loads((self.root / "candidate_input.json").read_text())
        self.assertEqual(len(truth["rows"]), 36)
        self.assertEqual(len(public["rows"]), 36)
        self.assertTrue(all(set(r) == {"opaque_id", "frame0", "frame1", "t", "epoch"}
                            for r in public["rows"]))
        self.assertTrue(all("approach" not in r["frame0"] and "native" not in r["frame0"]
                            and r["opaque_id"] in r["frame0"] for r in public["rows"]))
        pair = [r for r in truth["rows"] if r["variant"] == "native"
                and r["truth"].startswith("pixel_indistinguishable_")]
        self.assertEqual(len(pair), 2)
        self.assertEqual(pair[0]["sha256"], pair[1]["sha256"])

    def test_candidate_and_independent_audit_on_constructed_fixture(self):
        public = json.loads((self.root / "candidate_input.json").read_text())
        rows = [{"opaque_id": r["opaque_id"], **candidate.decide(r, self.root)}
                for r in public["rows"]]
        result = audit.audit(json.loads((self.root / "truth.json").read_text()),
                             public, {"rows": rows}, self.root)
        self.assertEqual(result["eligible_pass"], 9)
        self.assertEqual(result["rows_reconstructed"], 36)
        self.assertEqual(result["photometric_invariance_families"], 12)
        self.assertEqual(sum(result["mutation_rejections"].values()), 5)

    def test_candidate_is_truth_blind_and_never_safe(self):
        public = json.loads((self.root / "candidate_input.json").read_text())
        self.assertNotIn("truth", (self.root / "candidate_input.json").read_text())
        result = [candidate.decide(r, self.root) for r in public["rows"]]
        self.assertTrue(all(r.get("safe", False) is False for r in result))


if __name__ == "__main__":
    unittest.main()
