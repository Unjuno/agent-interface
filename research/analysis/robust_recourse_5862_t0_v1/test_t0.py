"""Construction checks only; no formal Docker allocation is consumed here."""
import copy
import importlib.util
import json
import pathlib
import unittest


ROOT = pathlib.Path(__file__).parent


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


candidate = load("candidate")
auditor = load("audit")
FIXTURE = json.loads((ROOT / "fixture.json").read_text(encoding="utf-8"))


class RobustRecourseT0Tests(unittest.TestCase):
    def test_all_seven_labels_reconstruct(self):
        report = auditor.audit(FIXTURE, candidate.run(FIXTURE))
        self.assertEqual(report["status"], "METHOD_PASS_SCOPED")

    def test_retry_is_only_existential_under_identical_blocked_belief(self):
        row = next(x for x in candidate.run(FIXTURE)["cases"] if x["id"] == "uncertain_delivery_same_blocked_receipt")
        self.assertEqual(row["label"], "ROBUST_ADVISORY")
        self.assertTrue(row["generic_retry_existential"])
        self.assertFalse(row["generic_retry_valid"])

    def test_no_route_is_bounded_not_global(self):
        row = next(x for x in candidate.run(FIXTURE)["cases"] if x["id"] == "target_genuinely_absent")
        self.assertEqual(row["label"], "NO_ROUTE_WITHIN_BOUND")

    def test_revoked_authority_and_manual_handoff_are_conditional(self):
        rows = {x["id"]: x for x in candidate.run(FIXTURE)["cases"]}
        self.assertEqual(rows["revoked_authority"]["label"], "CONDITIONAL_ADVISORY")
        self.assertEqual(rows["viable_manual_takeover"]["label"], "CONDITIONAL_ADVISORY")

    def test_mutation_removing_compatible_world_is_rejected(self):
        model = copy.deepcopy(FIXTURE)
        case = next(x for x in model["cases"] if x["id"] == "uncertain_delivery_same_blocked_receipt")
        case["belief"].remove("delivery_committed")
        with self.assertRaises(AssertionError):
            auditor.audit(model, candidate.run(model))

    def test_mutation_changing_one_identical_stop_receipt_is_rejected(self):
        model = copy.deepcopy(FIXTURE)
        model["states"]["delivery_committed"]["stop_receipt"]["completedPrefix"] = "different-prefix"
        with self.assertRaises(AssertionError):
            auditor.audit(model, candidate.run(model))

    def test_mutation_removing_adverse_duplicate_transition_is_rejected(self):
        model = copy.deepcopy(FIXTURE)
        move = model["states"]["delivery_committed"]["actions"]["retry"]
        move["outcomes"] = [x for x in move["outcomes"] if x["next"] != "UNSAFE"]
        with self.assertRaises(AssertionError):
            auditor.audit(model, candidate.run(model))

    def test_mutation_forged_authority_generation_is_rejected(self):
        model = copy.deepcopy(FIXTURE)
        model["states"]["approved"]["actions"]["act_after_approval"]["generation"] = 10
        with self.assertRaises(AssertionError):
            auditor.audit(model, candidate.run(model))

    def test_mutation_missing_precondition_is_rejected(self):
        model = copy.deepcopy(FIXTURE)
        model["states"]["stale_fresh"]["actions"]["act_target"]["preconditions"] = False
        with self.assertRaises(AssertionError):
            auditor.audit(model, candidate.run(model))

    def test_mutation_erasing_committed_effect_replay_marker_is_rejected(self):
        model = copy.deepcopy(FIXTURE)
        state = model["states"]["delivery_committed"]
        state["actions"]["retry"]["replays"] = []
        state["actions"]["retry"]["safe"] = True
        with self.assertRaises(AssertionError):
            auditor.audit(model, candidate.run(model))


if __name__ == "__main__":
    unittest.main()
