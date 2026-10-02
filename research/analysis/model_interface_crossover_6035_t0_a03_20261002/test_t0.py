from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

import auditor
import candidate


FIXTURE = json.loads((Path(__file__).parent / "fixture.json").read_text(encoding="utf-8"))


class CrossoverMethodTests(unittest.TestCase):
    def setUp(self) -> None:
        self.raw = candidate.build(FIXTURE)

    def test_scenario_dispositions(self) -> None:
        self.assertEqual(
            [row["disposition"] for row in self.raw["scenarios"]],
            ["NO_MATERIAL_INTERACTION", "INTERACTION_DETECTED", "FAIL_HARD_SAFETY", "HOLD_NO_COMMON_CONTRACT"],
        )

    def test_common_assigned_denominators_and_all_states_are_retained(self) -> None:
        self.assertEqual(self.raw["assigned_rows"], 64)
        for scenario in self.raw["scenarios"]:
            self.assertEqual(scenario["assigned_denominator_per_cell"], 4)
            for cell in scenario["cells"]:
                self.assertEqual(cell["assigned_denominator"], 4)
                self.assertEqual(sum(cell["terminal_counts"].values()), 4)
        states = {row["terminal"] for row in self.raw["rows"]}
        self.assertEqual(states, set(FIXTURE["terminal_states"]))

    def test_all_assigned_denominator_changes_the_rate(self) -> None:
        no_interaction = self.raw["scenarios"][0]
        profile_a_route_a = next(cell for cell in no_interaction["cells"] if cell["model"] == "profile_A" and cell["route"] == "route_A")
        self.assertEqual(profile_a_route_a["verified_success_fraction_all_assigned"], 0.5)
        self.assertEqual(profile_a_route_a["terminal_counts"]["TERMINAL_SAFE_STOP"], 1)

    def test_hard_safety_and_incomparability_override_statistical_pattern(self) -> None:
        self.assertEqual(self.raw["scenarios"][2]["disposition"], "FAIL_HARD_SAFETY")
        self.assertEqual(self.raw["scenarios"][3]["disposition"], "HOLD_NO_COMMON_CONTRACT")

    def test_independent_auditor_accepts_exact_raw(self) -> None:
        self.assertEqual(auditor.audit(FIXTURE, self.raw), [])

    def test_auditor_rejects_five_corruptions(self) -> None:
        corruptions = []
        missing_row = copy.deepcopy(self.raw)
        missing_row["rows"].pop()
        missing_row["assigned_rows"] -= 1
        corruptions.append(missing_row)

        status_changed = copy.deepcopy(self.raw)
        status_changed["rows"][0]["terminal"] = "VERIFIED_FAILURE"
        corruptions.append(status_changed)

        order_changed = copy.deepcopy(self.raw)
        order_changed["rows"][0]["start_order"] = 9
        corruptions.append(order_changed)

        safety_hidden = copy.deepcopy(self.raw)
        safety_row = next(row for row in safety_hidden["rows"] if row["forbidden_attempt"])
        safety_row["forbidden_attempt"] = False
        corruptions.append(safety_hidden)

        contract_hidden = copy.deepcopy(self.raw)
        contract_row = next(row for row in contract_hidden["rows"] if row["scenario"] == "noncomparable_contract" and row["contract"] == "tool-contract-v2")
        contract_row["contract"] = "tool-contract-v1"
        corruptions.append(contract_hidden)

        self.assertEqual(len(corruptions), 5)
        self.assertTrue(all(auditor.audit(FIXTURE, raw) for raw in corruptions))


if __name__ == "__main__":
    unittest.main()
