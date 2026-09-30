import unittest

import audit_race


class InvocationRaceAuditTests(unittest.TestCase):
    def raw(self):
        return {
            "schema": "owner_keyup_invocation_race_5156_t1_v1",
            "docker_invocations": 0,
            "x11_input_invocations": 0,
            "source_hashes": {"invoke_allocation.py": "a" * 64,
                              "race_guard.py": "b" * 64},
            "baseline": {"candidate_invocations": 2, "audit_invocations": 2,
                         "statuses": [0, 0]},
            "atomic_claim": {"candidate_invocations": 1, "audit_invocations": 1,
                              "statuses": [0, 2],
                              "claim_state": "RESERVED_NO_RETRY"},
        }

    def test_independent_auditor_accepts_the_declared_baseline_and_fix_bounds(self):
        raw = self.raw()
        self.assertEqual(audit_race.audit_records(raw, raw["source_hashes"]), [])

    def test_independent_auditor_rejects_a_second_fixed_candidate(self):
        raw = self.raw()
        raw["atomic_claim"]["candidate_invocations"] = 2
        self.assertIn("atomic claim admitted an unexpected candidate count",
                      audit_race.audit_records(raw, raw["source_hashes"]))

    def test_independent_auditor_rejects_any_container_or_input_invocation(self):
        raw = self.raw()
        raw["docker_invocations"] = 1
        self.assertIn("experiment exceeded host-only scope",
                      audit_race.audit_records(raw, raw["source_hashes"]))

    def test_independent_auditor_rejects_source_hash_drift(self):
        raw = self.raw()
        actual = dict(raw["source_hashes"])
        actual["race_guard.py"] = "c" * 64
        self.assertIn("source hash mismatch: race_guard.py",
                      audit_race.audit_records(raw, actual))


if __name__ == "__main__":
    unittest.main()
