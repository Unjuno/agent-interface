import json
import hashlib
import unittest
from pathlib import Path

import auditor
import candidate


class ProvenanceContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = Path(__file__).parent
        cls.fixture = json.loads((cls.root / "fixture.json").read_text())

    def run_candidate(self):
        raw = candidate.pipeline(self.fixture)
        raw["fixture_sha256"] = hashlib.sha256((self.root / "fixture.json").read_bytes()).hexdigest()
        raw["candidate_sha256"] = hashlib.sha256((self.root / "candidate.py").read_bytes()).hexdigest()
        return raw

    def test_application_model_and_unknown_text_are_not_authority(self):
        raw = self.run_candidate()
        self.assertEqual(auditor.audit(raw, self.fixture), [])
        self.assertEqual([x["id"] for x in raw["authorized_intents"]], ["u3", "u1"])
        self.assertNotIn("app2", [x["id"] for x in raw["authorized_intents"]])
        self.assertNotIn("hyp2", [x["id"] for x in raw["authorized_intents"]])
        self.assertNotIn("unknown1", [x["id"] for x in raw["authorized_intents"]])

    def test_summary_and_retrieval_keep_source_refs_but_not_authority(self):
        raw = self.run_candidate()
        summary = next(x for x in raw["summaries"] if "Quarterly Plan" in x["text"])
        self.assertEqual(summary["source_refs"], ["app:document:7"])
        self.assertEqual(summary["authority_class"], "DESCRIPTIVE_ONLY")
        self.assertTrue(all(x["source_refs"] for x in raw["retrieved"] if x["source_status"] == "BOUND"))

    def test_superseded_revision_and_corruption_controls(self):
        raw = self.run_candidate()
        self.assertEqual(auditor.audit(raw, self.fixture), [])
        for name, changed in auditor.mutations(raw).items():
            with self.subTest(name=name):
                self.assertTrue(auditor.audit(changed, self.fixture))


if __name__ == "__main__":
    unittest.main()
