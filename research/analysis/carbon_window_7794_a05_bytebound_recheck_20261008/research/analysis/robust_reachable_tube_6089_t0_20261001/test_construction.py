import copy
import json
import unittest
from pathlib import Path
import audit
import candidate

ROOT = Path(__file__).parent
DATA = json.loads((ROOT / "cases.json").read_text(encoding="utf-8"))
RESULT = candidate.run(DATA)


class TubeTests(unittest.TestCase):
    def test_method_audit_passes(self):
        self.assertEqual(audit.audit(DATA, RESULT)["disposition"], "PASS_METHOD_SCOPED")

    def test_safe_corridor_uses_largest_horizon(self):
        row = next(x for x in RESULT["results"] if x["id"] == "safe_corridor_wide")
        self.assertEqual(row["policies"]["ROBUST_TUBE"]["horizon"], 4)

    def test_near_boundary_releases_shorter_than_corridor(self):
        horizons = {x["id"]: x["policies"]["ROBUST_TUBE"]["horizon"] for x in RESULT["results"] if x["disposition"] == "EVALUATED"}
        self.assertLess(horizons["near_upper_boundary"], horizons["safe_corridor_wide"])

    def test_release_in_flight_is_inside_the_gate(self):
        row = next(x for x in RESULT["results"] if x["id"] == "release_in_flight_boundary")
        self.assertEqual(row["policies"]["ROBUST_TUBE"]["horizon"], 1)
        self.assertEqual(row["policies"]["ROBUST_TUBE"]["tube"][-1]["tick"], 2)

    def test_invalid_model_and_target_yield(self):
        for cid, expected in (("invalid_model", "YIELD_MODEL_INVALID"), ("invalid_target", "YIELD_TARGET_INVALID")):
            row = next(x for x in RESULT["results"] if x["id"] == cid)
            self.assertEqual(row["disposition"], expected)
            self.assertEqual(row["policies"], {})

    def test_mutation_omitted_prefix_detected(self):
        bad = copy.deepcopy(RESULT)
        row = next(x for x in bad["results"] if x["id"] == "safe_corridor_wide")
        row["policies"]["ROBUST_TUBE"]["tube"].pop(2)
        self.assertNotEqual(audit.audit(DATA, bad)["disposition"], "PASS_METHOD_SCOPED")

    def test_mutation_ignored_release_lag_detected(self):
        bad = copy.deepcopy(RESULT)
        row = next(x for x in bad["results"] if x["id"] == "safe_corridor_wide")
        row["policies"]["ROBUST_TUBE"]["release_tick"] -= 1
        self.assertNotEqual(audit.audit(DATA, bad)["disposition"], "PASS_METHOD_SCOPED")

    def test_mutation_stale_identity_detected(self):
        bad = copy.deepcopy(DATA)
        bad["allocation_id"] = "STALE"
        self.assertIn("allocation_binding", audit.audit(bad, RESULT)["errors"])

    def test_mutation_underestimated_disturbance_detected(self):
        bad = copy.deepcopy(DATA)
        bad["disturbances"] = [0]
        self.assertNotEqual(audit.audit(bad, RESULT)["disposition"], "PASS_METHOD_SCOPED")


if __name__ == "__main__": unittest.main(verbosity=2)
