import copy
import json
import unittest
from pathlib import Path

from audit_case import audit


CASE = json.loads(Path(__file__).with_name("CASE.json").read_text())


class IndependentNoLeaseAuditTests(unittest.TestCase):
    def test_retained_a17_trace_slice_is_a_verified_no_lease_passive_refresh(self):
        result = audit(CASE)
        self.assertEqual(result["status"], "PASS")
        self.assertTrue(all(result["checks"].values()))

    def test_public_token_and_x11_identifiers_must_be_pseudonymized(self):
        case = copy.deepcopy(CASE)
        case["accepted_event"]["intent_token"] = "unredacted-value"
        self.assertEqual(audit(case)["status"], "FAIL")
        case = copy.deepcopy(CASE)
        case["fresh_observation"]["signals"]["health"]["binding"]["surface"] = 999999
        self.assertEqual(audit(case)["status"], "FAIL")

    def test_input_admission_for_refresh_fails_closed(self):
        case = copy.deepcopy(CASE)
        case["matching_input_admission_count"] = 1
        self.assertEqual(audit(case)["status"], "FAIL")

    def test_input_admission_count_requires_exact_integer_zero(self):
        for value in (False, 0.0):
            with self.subTest(value=value):
                case = copy.deepcopy(CASE)
                case["matching_input_admission_count"] = value
                self.assertEqual(audit(case)["status"], "FAIL")

    def test_missing_prior_active_lease_release_fails_closed(self):
        case = copy.deepcopy(CASE)
        case["preceding_active_program"]["input_release"]["owner_release"]["verified"] = False
        self.assertEqual(audit(case)["status"], "FAIL")

    def test_prior_owner_release_errors_fail_closed(self):
        case = copy.deepcopy(CASE)
        case["preceding_active_program"]["input_release"]["owner_release"][
            "key_state_errors"] = ["query failed"]
        self.assertEqual(audit(case)["status"], "FAIL")

    def test_prior_owner_release_event_and_reason_must_be_cancelled_release(self):
        mutations = (
            ("event", "wrong-event"),
            ("event", None),
            ("reason", "release"),
            ("reason", None),
        )
        for field, value in mutations:
            with self.subTest(field=field, value=value):
                case = copy.deepcopy(CASE)
                owner_release = case["preceding_active_program"][
                    "input_release"]["owner_release"]
                if value is None:
                    owner_release.pop(field)
                else:
                    owner_release[field] = value
                self.assertEqual(audit(case)["status"], "FAIL")

    def test_prior_admission_identity_and_token_must_match(self):
        for field, value in (("id", "other-program"), ("intent_token", "other-token")):
            with self.subTest(field=field):
                case = copy.deepcopy(CASE)
                case["preceding_active_program"]["input_admissions"][0][field] = value
                self.assertEqual(audit(case)["status"], "FAIL")

    def test_cancel_release_and_terminal_must_share_admission_identity(self):
        for section in ("cancel_requested", "input_release", "terminal"):
            with self.subTest(section=section):
                case = copy.deepcopy(CASE)
                case["preceding_active_program"][section]["id"] = "other-program"
                self.assertEqual(audit(case)["status"], "FAIL")

    def test_prior_cancel_release_terminal_order_must_be_monotonic(self):
        mutations = (
            lambda c: c["preceding_active_program"]["input_release"][
                "owner_release"].__setitem__("verified_ns", 1),
            lambda c: c["preceding_active_program"]["terminal"].__setitem__(
                "terminal_ns", 1),
            lambda c: c["preceding_active_program"]["terminal"].__setitem__(
                "terminal_ns", c["preceding_active_program"]["input_release"][
                    "owner_release"]["verified_ns"] - 1),
        )
        for mutate in mutations:
            with self.subTest(mutate=mutate):
                case = copy.deepcopy(CASE)
                mutate(case)
                self.assertEqual(audit(case)["status"], "FAIL")

    def test_nonempty_or_unknown_passive_release_fails_closed(self):
        for field, value in (("keys_down", ["space"]), ("buttons_down", ["fire"]),
                             ("keys_unknown", ["W"]), ("key_state_errors", ["query failed"])):
            with self.subTest(field=field):
                case = copy.deepcopy(CASE)
                case["terminal_event"]["release"][field] = value
                self.assertEqual(audit(case)["status"], "FAIL")

    def test_nonobserve_command_fails_closed(self):
        case = copy.deepcopy(CASE)
        case["refresh_command"]["steps"] = [{"op": "press", "key": "space"}]
        self.assertEqual(audit(case)["status"], "FAIL")

    def test_non_null_mismatched_release_token_fails_closed(self):
        case = copy.deepcopy(CASE)
        case["terminal_event"]["release"]["intent_token"] = "different"
        self.assertEqual(audit(case)["status"], "FAIL")

    def test_steps_completed_requires_exact_integer_one(self):
        for value in (True, 1.0):
            with self.subTest(value=value):
                case = copy.deepcopy(CASE)
                case["terminal_event"]["steps_completed"] = value
                self.assertEqual(audit(case)["status"], "FAIL")


if __name__ == "__main__":
    unittest.main()
