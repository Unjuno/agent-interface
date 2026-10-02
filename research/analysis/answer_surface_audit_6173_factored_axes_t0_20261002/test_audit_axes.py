import json
from pathlib import Path
import unittest

from audit_axes import audit, derive_axes_observer

HERE = Path(__file__).resolve().parent


def fixture():
    return json.loads((HERE / "fixture.json").read_text())


def correct_candidate(fx):
    return {"allocation_id": "allocation", "source_main_sha": "main",
            "candidate_invocations": 1, "fixture_sha256": "fixture",
            "cases": [{"case_id": row["case_id"], "axes": derive_axes_observer(row["observer"])}
                      for row in fx["cases"]]}


def run(fx, candidate=None):
    return audit(candidate or correct_candidate(fx), fx, "fixture", "allocation", "main")


class AuditAxesTests(unittest.TestCase):
    def test_independent_reconstruction_accepts_all_frozen_cases(self):
        result = run(fixture())
        self.assertEqual(result["status"], "PASS_METHOD_FACTORED_AXES")
        self.assertEqual(result["case_count"], 17)
        self.assertEqual(result["errors"], [])

    def test_rejects_attempt_axis_collapse_under_monitor_gap(self):
        fx = fixture()
        output = correct_candidate(fx)
        output["cases"][3]["axes"]["attempt_axis"]["status"] = "NO_ATTEMPT_OBSERVED"
        self.assertEqual(run(fx, output)["status"], "FAIL_AUDIT")

    def test_rejects_response_deletion_from_candidate_projection(self):
        fx = fixture()
        fx["cases"][2]["candidate_view"]["events"].pop()
        self.assertEqual(run(fx)["status"], "FAIL_AUDIT")

    def test_rejects_forged_flat_disposition_and_self_claim_override(self):
        fx = fixture()
        output = correct_candidate(fx)
        output["cases"][13]["axes"]["disposition"] = "NO_ORACLE_ACCESS_OBSERVED"
        self.assertEqual(run(fx, output)["status"], "FAIL_AUDIT")

    def test_rejects_forged_provenance(self):
        fx = fixture()
        output = correct_candidate(fx)
        output["source_main_sha"] = "other"
        self.assertEqual(run(fx, output)["status"], "FAIL_AUDIT")


if __name__ == "__main__":
    unittest.main()
