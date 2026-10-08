import importlib.util
import json
import pathlib
import unittest


HERE = pathlib.Path(__file__).resolve().parent


def load(name):
    spec = importlib.util.spec_from_file_location(name, HERE / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


CANDIDATE = load("candidate")
AUDIT = load("audit")


class GuardProposalRiskT0(unittest.TestCase):
    def setUp(self):
        self.fixture = json.loads((HERE / "fixture.json").read_text(encoding="utf-8"))
        self.result = CANDIDATE.run(self.fixture)

    def test_frozen_result_passes_independent_raw_only_audit(self):
        result = AUDIT.audit(self.fixture, self.result)
        self.assertEqual(result["disposition"], "PASS_METHOD_SCOPED")
        self.assertEqual(result["world_count"], 3)
        self.assertEqual(result["arm_rows"], 6)
        self.assertEqual(result["errors"], [])

    def test_compensation_changes_harm_despite_same_guard(self):
        gate = AUDIT.audit(self.fixture, self.result)["gate"]
        self.assertEqual(gate["compensation_harm_per_1000"], [50, 60])
        self.assertEqual(gate["unsafe_rejection_sensitivity"], 0.9)
        self.assertEqual(gate["safe_false_rejection_rate"], 0.0)

    def test_null_preserves_policy_mix_and_guard_reduces_harm(self):
        gate = AUDIT.audit(self.fixture, self.result)["gate"]
        self.assertEqual(gate["null_harm_per_1000"], [50, 5])
        self.assertEqual(gate["protective_guard_harm_per_1000"], 2)

    def test_denominator_never_conditions_on_admission(self):
        for world in self.result["worlds"]:
            for row in world["arms"]:
                self.assertEqual(row["opportunities"], 1000)
                self.assertEqual(row["proposals"], 1000)
                self.assertEqual(row["harmful_admissions"] + row["unsafe_rejected"], row["unsafe_proposals"])

    def test_auditor_rejects_deleted_arm(self):
        damaged = json.loads(json.dumps(self.result))
        damaged["worlds"][0]["arms"].pop()
        self.assertEqual(AUDIT.audit(self.fixture, damaged)["disposition"], "FAIL_AUDIT")

    def test_auditor_rejects_wrong_harm_count(self):
        damaged = json.loads(json.dumps(self.result))
        damaged["worlds"][0]["arms"][1]["harmful_admissions"] -= 1
        self.assertEqual(AUDIT.audit(self.fixture, damaged)["disposition"], "FAIL_AUDIT")

    def test_auditor_rejects_admission_conditioned_denominator(self):
        damaged = json.loads(json.dumps(self.result))
        damaged["worlds"][0]["arms"][1]["opportunities"] = 400
        self.assertEqual(AUDIT.audit(self.fixture, damaged)["disposition"], "FAIL_AUDIT")

    def test_auditor_rejects_unaccounted_retries(self):
        damaged = json.loads(json.dumps(self.result))
        damaged["worlds"][0]["arms"][1]["retries"] = 0
        self.assertEqual(AUDIT.audit(self.fixture, damaged)["disposition"], "FAIL_AUDIT")


if __name__ == "__main__":
    unittest.main()
