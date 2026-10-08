#!/usr/bin/env python3
"""Construction-only checks on authored inline cases; never reads formal fixture."""
import hashlib
import unittest

from candidate import simulate
from auditor import ALLOCATION, canon, expected_rows, mutations_rejected, valid


def job(identity, principal, arrival, service, deadline, eligible_until, mandatory=False):
    return {"id": identity, "principal": principal, "arrival": arrival, "service": service,
            "deadline": deadline, "eligible_until": eligible_until, "mandatory": mandatory}


class ConstructionTests(unittest.TestCase):
    def trace(self, tasks):
        return {"seed": -1, "stratum": "construction_inline", "tasks": tasks}

    def test_edf_prefers_earlier_deadline_among_ready_jobs(self):
        t = self.trace([job("A0", "A", 0, 4, 12, 20), job("B0", "B", 0, 1, 4, 20)])
        result = simulate(t, "edf")
        self.assertEqual(result["decisions"][0]["id"], "B0")

    def test_service_must_fit_hard_eligibility_horizon(self):
        t = self.trace([job("block", "A", 0, 2, 20, 20), job("expires", "B", 0, 2, 8, 3)])
        result = simulate(t, "fifo")
        expired = next(d for d in result["decisions"] if d["id"] == "expires")
        self.assertEqual(expired["status"], "expired_not_dispatched")
        self.assertIsNone(expired["wait_to_dispatch"])

    def test_exact_horizon_boundary_is_allowed(self):
        t = self.trace([job("edge", "A", 0, 3, 3, 3)])
        result = simulate(t, "fifo")
        self.assertEqual(result["decisions"][0]["finish"], 3)
        self.assertTrue(result["decisions"][0]["on_time"])

    def test_mandatory_work_precedes_optional_at_available_boundary(self):
        t = self.trace([job("A0", "A", 0, 4, 10, 20),
                        job("SYS-release", "SYSTEM", 1, 1, 2, None, True)])
        result = simulate(t, "fifo")
        completed = [d["id"] for d in result["decisions"] if d["status"] == "completed"]
        self.assertEqual(completed, ["A0", "SYS-release"])
        self.assertEqual(next(d["start"] for d in result["decisions"] if d["id"] == "SYS-release"), 4)

    def test_independent_auditor_rejects_five_inline_raw_corruptions(self):
        fixture = {"allocation_id": ALLOCATION, "traces": [{"seed": -2,
            "stratum": "revocation_mandatory", "tasks": [
                job("A0", "A", 0, 2, 6, 10), job("B0", "B", 1, 1, 5, 9),
                job("SYS-release", "SYSTEM", 2, 1, 3, None, True)]}]}
        fixture_bytes = (canon(fixture) + "\n").encode()
        expected = expected_rows(fixture)
        payload = {"allocation_id": ALLOCATION,
                   "fixture_sha256": hashlib.sha256(fixture_bytes).hexdigest(),
                   "rows": expected,
                   "scope": "finite authored synthetic method-only result; not a live fairness claim"}
        self.assertTrue(valid(payload, fixture, fixture_bytes, expected))
        self.assertEqual(mutations_rejected(payload, fixture, fixture_bytes, expected), 5)


if __name__ == "__main__":
    unittest.main()
