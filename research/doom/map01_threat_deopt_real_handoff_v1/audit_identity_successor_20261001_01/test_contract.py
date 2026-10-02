"""Pre-freeze in-memory checks; does not write candidate or audit outputs."""
import copy
import json
import unittest
from pathlib import Path

import audit
import candidate
import legacy_audit

HERE = Path(__file__).resolve().parent
FIXTURE_BYTES = (HERE / "fixture.json").read_bytes()
FIXTURE = json.loads(FIXTURE_BYTES)


class IdentityContract(unittest.TestCase):
    def setUp(self):
        self.rows = [candidate.row(case, FIXTURE) for case in FIXTURE["cases"]]
        self.raw = {"schema": "map01-threat-deopt-626-audit-identity-raw-v1",
                    "fixture_sha256": audit.hashlib.sha256(FIXTURE_BYTES).hexdigest(),
                    "rows": self.rows}

    def test_pristine_semantics_pass_both_auditors(self):
        self.assertEqual(audit.audit(self.raw, FIXTURE, FIXTURE_BYTES)["errors"], [])
        self.assertEqual(legacy_audit.audit(self.rows)["errors"], [])

    def test_new_auditor_binds_each_identity_field(self):
        mutations = {
            "id": (0, "rh99-baseline"),
            "runtime_bundle_sha256": (0, "0" * 64),
            "fixture_id": (0, "other-fixture"),
            "fixture_seed": (0, 1),
            "arm": (0, "candidate"),
        }
        for key, (index, value) in mutations.items():
            with self.subTest(field=key):
                changed = copy.deepcopy(self.raw)
                changed["rows"][index][key] = value
                self.assertNotEqual(audit.audit(changed, FIXTURE, FIXTURE_BYTES)["errors"], [])

    def test_new_auditor_rejects_incomplete_schedule(self):
        changed = copy.deepcopy(self.raw)
        changed["rows"].pop()
        self.assertIn("case_completeness", audit.audit(changed, FIXTURE, FIXTURE_BYTES)["errors"])

    def test_old_auditor_reproduces_four_identity_blind_spots(self):
        for key, value in (("id", "rh99-baseline"),
                           ("runtime_bundle_sha256", "0" * 64),
                           ("fixture_id", "other-fixture"),
                           ("fixture_seed", 1)):
            with self.subTest(field=key):
                changed = copy.deepcopy(self.rows)
                changed[0][key] = value
                self.assertEqual(legacy_audit.audit(changed)["errors"], [])


if __name__ == "__main__":
    unittest.main()
