import json
import unittest
from pathlib import Path

import auditor
import candidate


ROOT = Path(__file__).parent


class ContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = json.loads((ROOT / "fixture.json").read_text())
        cls.policy = json.loads((ROOT / "policy.json").read_text())
        cls.oracle = json.loads((ROOT / "expected.json").read_text())
        cls.rows = candidate.run(cls.fixture, cls.policy)

    def test_all_frozen_rows_reconcile(self):
        self.assertEqual(33, len(self.rows))
        self.assertEqual("PASS_METHOD_SCOPED", auditor.audit(self.fixture, self.policy, self.oracle, self.rows)["status"])

    def test_same_label_actor_allowed_vs_wrong_recipient(self):
        rows = {(r["case_id"], r["mode"]): r for r in self.rows}
        self.assertEqual("ALLOWED", rows[("F01_ALLOWED_SCHEDULER", "CONTEXT_BOUND")]["decision"])
        self.assertEqual("BLOCKED_FLOW", rows[("F02_WRONG_RECIPIENT", "CONTEXT_BOUND")]["decision"])
        self.assertEqual("ALLOWED", rows[("F02_WRONG_RECIPIENT", "ACTOR_ONLY")]["decision"])
        self.assertEqual("BLOCKED_FLOW", rows[("F01_ALLOWED_SCHEDULER", "LABEL_ONLY")]["decision"])

    def test_same_recipient_wrong_purpose_is_blocked(self):
        rows = {(r["case_id"], r["mode"]): r for r in self.rows}
        self.assertEqual("BLOCKED_FLOW", rows[("F03_WRONG_PURPOSE", "CONTEXT_BOUND")]["decision"])

    def test_explicit_release_is_exact_and_scoped(self):
        row = next(r for r in self.rows if r["case_id"] == "F04_EXPLICIT_SCOPED_RELEASE" and r["mode"] == "CONTEXT_BOUND")
        self.assertEqual("DECLASSIFIED", row["decision"])
        self.assertEqual(["availability"], row["released_fields"])

    def test_missing_context_and_low_integrity_fail_closed(self):
        rows = {(r["case_id"], r["mode"]): r for r in self.rows}
        self.assertEqual("UNKNOWN_FLOW", rows[("F05_MISSING_RECIPIENT", "CONTEXT_BOUND")]["decision"])
        self.assertEqual("UNKNOWN_FLOW", rows[("F06_MISSING_PURPOSE", "CONTEXT_BOUND")]["decision"])
        self.assertEqual("BLOCKED_FLOW", rows[("F08_LOW_INTEGRITY_SOURCE", "CONTEXT_BOUND")]["decision"])
        self.assertEqual("BLOCKED_FLOW", rows[("F09_STALE_RELEASE", "CONTEXT_BOUND")]["decision"])

    def test_public_label_is_allowed_and_opaque_label_fails_closed(self):
        rows = {(r["case_id"], r["mode"]): r for r in self.rows}
        self.assertEqual("ALLOWED", rows[("F10_KNOWN_PUBLIC", "CONTEXT_BOUND")]["decision"])
        self.assertEqual(["status"], rows[("F10_KNOWN_PUBLIC", "CONTEXT_BOUND")]["released_fields"])
        self.assertEqual("UNKNOWN_FLOW", rows[("F11_OPAQUE_SOURCE", "CONTEXT_BOUND")]["decision"])
        self.assertEqual([], rows[("F11_OPAQUE_SOURCE", "CONTEXT_BOUND")]["released_fields"])

    def test_nine_frozen_corruptions_are_rejected(self):
        mutations = []
        for predicate, mutate in [
            (lambda r: r["case_id"] == "F02_WRONG_RECIPIENT" and r["mode"] == "CONTEXT_BOUND", lambda r: r.update(decision="ALLOWED", released_fields=["availability"])),
            (lambda r: r["case_id"] == "F03_WRONG_PURPOSE" and r["mode"] == "CONTEXT_BOUND", lambda r: r.update(decision="ALLOWED", released_fields=["availability"])),
            (lambda r: r["case_id"] == "F04_EXPLICIT_SCOPED_RELEASE" and r["mode"] == "CONTEXT_BOUND", lambda r: r.update(released_fields=["availability", "diagnosis"])),
            (lambda r: r["case_id"] == "F05_MISSING_RECIPIENT" and r["mode"] == "CONTEXT_BOUND", lambda r: r.update(decision="ALLOWED", released_fields=["availability"])),
            (lambda r: r["case_id"] == "F04_EXPLICIT_SCOPED_RELEASE" and r["mode"] == "CONTEXT_BOUND", lambda r: r.update(recipient="public-channel")),
            (lambda r: r["case_id"] == "F01_ALLOWED_SCHEDULER" and r["mode"] == "CONTEXT_BOUND", lambda r: r.update(source_digest="mutated")),
            (lambda r: r["case_id"] == "F08_LOW_INTEGRITY_SOURCE" and r["mode"] == "CONTEXT_BOUND", lambda r: r.update(decision="ALLOWED", released_fields=["target-id"])),
            (lambda r: r["case_id"] == "F01_ALLOWED_SCHEDULER" and r["mode"] == "CONTEXT_BOUND", lambda r: r.update(unapproved_extra_field="hidden-data")),
            (lambda r: r["case_id"] == "F11_OPAQUE_SOURCE" and r["mode"] == "CONTEXT_BOUND", lambda r: r.update(decision="ALLOWED", released_fields=["availability"])),
        ]:
            broken = json.loads(json.dumps(self.rows))
            target = next(row for row in broken if predicate(row))
            mutate(target)
            with self.assertRaises(ValueError):
                auditor.audit(self.fixture, self.policy, self.oracle, broken)
            mutations.append(True)
        self.assertEqual(9, len(mutations))


if __name__ == "__main__":
    unittest.main()
