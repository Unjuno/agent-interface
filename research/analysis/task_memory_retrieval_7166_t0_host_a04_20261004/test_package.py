#!/usr/bin/env python3
"""Construction tests; formal candidate/auditor are invoked separately once."""
import json
import tempfile
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
import build_fixture
import candidate
import auditor


class PackageTests(unittest.TestCase):
    def test_fixture_has_72_balanced_cases(self):
        with tempfile.TemporaryDirectory() as tmp:
            old = build_fixture.ROOT
            build_fixture.ROOT = Path(tmp)
            try:
                build_fixture.main()
                fixture = json.loads((Path(tmp) / "fixture.json").read_text())
                self.assertEqual(len(fixture["cases"]), 72)
                self.assertEqual(len({c["case_id"] for c in fixture["cases"]}), 72)
                self.assertEqual(set(build_fixture.json.loads((Path(tmp) / "oracle.json").read_text())["expected_counts"].values()), {12})
            finally:
                build_fixture.ROOT = old

    def test_selection_contract_labels(self):
        base = {"history_required": True, "identity_unique": True, "source_hash": "bad", "lineage_linear": True, "source": {"event_ids": ["a", "b"]}}
        self.assertEqual(candidate.choose({**base, "history_required": False}), "NONE")
        self.assertEqual(candidate.choose(base), "ABSTAIN")
        self.assertEqual(candidate.choose({**base, "identity_unique": False}), "ABSTAIN")
        self.assertEqual(candidate.choose({**base, "lineage_linear": False}), "ABSTAIN")

    def test_auditor_accepts_and_rejects_six_controls(self):
        with tempfile.TemporaryDirectory() as tmp:
            old = build_fixture.ROOT
            build_fixture.ROOT = Path(tmp)
            try:
                build_fixture.main()
                fixture = json.loads((Path(tmp) / "fixture.json").read_text())
                rows = []
                for c in fixture["cases"]:
                    label = "NONE" if c["task_need"] == "current_only" else ("ABSTAIN" if not c["identity_unique"] or not c["source_hash"] or not c["lineage_linear"] else "EVENT_CHAIN")
                    rows.append({"case_id": c["case_id"], "label": label, "source_hash": c["source_hash"], "event_ids": c["source"]["event_ids"] if label == "EVENT_CHAIN" else [], "authority_granted": False, "authority_scope": None})
                self.assertEqual(auditor.audit_rows(fixture["cases"], rows), (True, "PASS"))
                cases = fixture["cases"]
                controls = [
                    lambda x: x[0].__setitem__("label", "ABSTAIN"),
                    lambda x: x[12].__setitem__("source_hash", "0" * 64),
                    lambda x: x[24].__setitem__("label", "EVENT_CHAIN"),
                    lambda x: x[0].__setitem__("authority_granted", True),
                    lambda x: x[12].__setitem__("event_ids", ["bad"]),
                    lambda x: x[48].__setitem__("label", "EVENT_CHAIN"),
                ]
                for mutate in controls:
                    changed = json.loads(json.dumps(rows))
                    mutate(changed)
                    self.assertFalse(auditor.audit_rows(cases, changed)[0])
            finally:
                build_fixture.ROOT = old

    def test_every_mutation_changes_raw_rows(self):
        rows = [{"label": "NONE", "source_hash": "a", "event_ids": [], "authority_granted": False} for _ in range(72)]
        for name, mutate in auditor.mutations().items():
            changed = json.loads(json.dumps(rows))
            mutate(changed)
            self.assertNotEqual(changed, rows, name)


if __name__ == "__main__":
    unittest.main()
