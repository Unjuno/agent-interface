"""Contract tests for the #6501 deterministic singleflight candidate."""

import copy
import json
import tempfile
import unittest
from pathlib import Path

from candidate import run


class ScopeTypedSingleflightTests(unittest.TestCase):
    def test_equivalent_overlapping_requests_share_one_read(self):
        result = run("fixtures.json")
        case = result["cases"]["equivalent_overlap"]
        self.assertEqual(case["scope_typed"]["verifier_invocations"], 1)
        self.assertEqual(case["no_coalescing"]["verifier_invocations"], 2)
        self.assertLess(
            sum(case["scope_typed"]["decision_latency_ms"].values()),
            sum(case["no_coalescing"]["decision_latency_ms"].values()),
        )
        self.assertEqual(
            case["scope_typed"]["per_caller"],
            {"a": "ADMISSIBLE_TRUE", "b": "ADMISSIBLE_TRUE"},
        )

    def test_same_predicate_on_other_target_never_inherits_owner_result(self):
        result = run("fixtures.json")
        case = result["cases"]["different_target"]
        self.assertEqual(case["naive_predicate_key"]["per_caller"]["b"], "WRONG_SHARED_TRUE")
        self.assertEqual(case["scope_typed"]["verifier_invocations"], 2)
        self.assertEqual(case["scope_typed"]["per_caller"]["b"], "ADMISSIBLE_FALSE")

    def test_generation_change_before_return_makes_every_waiter_stale(self):
        result = run("fixtures.json")
        case = result["cases"]["generation_flip"]
        self.assertEqual(case["scope_typed"]["verifier_invocations"], 1)
        self.assertEqual(
            case["scope_typed"]["per_caller"],
            {"a": "STALE_ON_RETURN", "b": "STALE_ON_RETURN"},
        )

    def test_each_waiter_enforces_its_own_deadline(self):
        result = run("fixtures.json")
        case = result["cases"]["disjoint_deadlines"]
        self.assertEqual(case["scope_typed"]["verifier_invocations"], 1)
        self.assertEqual(
            case["scope_typed"]["per_caller"],
            {"early": "DEADLINE_MISSED", "late": "ADMISSIBLE_TRUE"},
        )

    def test_cancelling_one_waiter_does_not_cancel_another_or_grant_authority(self):
        result = run("fixtures.json")
        case = result["cases"]["cancelled_waiter"]
        self.assertEqual(case["scope_typed"]["verifier_invocations"], 1)
        self.assertEqual(
            case["scope_typed"]["per_caller"],
            {"cancelled": "CANCELLED_WAITER", "survivor": "ADMISSIBLE_TRUE"},
        )

    def test_owner_failure_is_not_retried_or_upgraded(self):
        result = run("fixtures.json")
        case = result["cases"]["owner_failure"]
        self.assertEqual(case["scope_typed"]["verifier_invocations"], 1)
        self.assertEqual(case["scope_typed"]["per_caller"], {"a": "OWNER_FAILED", "b": "OWNER_FAILED"})

    def test_unknown_and_contradictory_evidence_remain_per_caller(self):
        result = run("fixtures.json")
        unknown = result["cases"]["unknown_result"]["scope_typed"]
        contradictory = result["cases"]["contradictory_dependencies"]["scope_typed"]
        self.assertEqual(unknown["per_caller"], {"a": "UNKNOWN", "b": "UNKNOWN"})
        self.assertEqual(contradictory["verifier_invocations"], 2)
        self.assertEqual(
            contradictory["per_caller"],
            {"a": "ADMISSIBLE_TRUE", "b": "ADMISSIBLE_FALSE"},
        )

    def test_restart_aba_with_reused_generation_number_is_distinct_scope(self):
        result = run("fixtures.json")
        case = result["cases"]["restart_aba"]
        self.assertEqual(case["scope_typed"]["verifier_invocations"], 2)
        self.assertEqual(case["scope_typed"]["per_caller"]["after_restart"], "ADMISSIBLE_FALSE")

    def test_late_request_after_completion_starts_a_fresh_read(self):
        result = run("fixtures.json")
        case = result["cases"]["late_after_completion"]
        self.assertEqual(case["scope_typed"]["verifier_invocations"], 2)
        self.assertEqual(case["scope_typed"]["per_caller"]["late"], "ADMISSIBLE_TRUE")

    def test_all_frozen_cases_are_present_once(self):
        result = run("fixtures.json")
        self.assertEqual(
            set(result["cases"]),
            {
                "equivalent_overlap",
                "different_target",
                "generation_flip",
                "disjoint_deadlines",
                "cancelled_waiter",
                "owner_failure",
                "unknown_result",
                "contradictory_dependencies",
                "restart_aba",
                "late_after_completion",
            },
        )

    def test_every_frozen_scope_field_splits_non_equivalent_calls(self):
        base = json.loads(Path("fixtures.json").read_text(encoding="utf-8"))
        for field in base["scope_fields"]:
            with self.subTest(field=field):
                fixtures = copy.deepcopy(base)
                case = next(row for row in fixtures["cases"] if row["id"] == "equivalent_overlap")
                original = case["scope"][field]
                if isinstance(original, dict):
                    changed = {**original, "mutation": "different"}
                elif isinstance(original, int):
                    changed = original + 1
                else:
                    changed = original + "-different"
                case["requests"][1]["scope_override"] = {field: changed}
                with tempfile.TemporaryDirectory() as temp_dir:
                    path = Path(temp_dir) / "fixtures.json"
                    path.write_text(json.dumps(fixtures), encoding="utf-8")
                    output = run(path)
                self.assertEqual(
                    output["cases"]["equivalent_overlap"]["scope_typed"]["verifier_invocations"],
                    2,
                )

    def test_arrival_before_completion_joins_but_after_completion_does_not(self):
        fixtures = json.loads(Path("fixtures.json").read_text(encoding="utf-8"))
        case = next(row for row in fixtures["cases"] if row["id"] == "late_after_completion")
        case["requests"][1]["at_ms"] = 4
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "fixtures.json"
            path.write_text(json.dumps(fixtures), encoding="utf-8")
            output = run(path)
        self.assertEqual(output["cases"]["late_after_completion"]["scope_typed"]["verifier_invocations"], 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
