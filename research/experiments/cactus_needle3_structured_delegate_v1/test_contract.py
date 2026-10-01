import json
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
CASES = json.loads((HERE / "CASES.json").read_text(encoding="utf-8"))


class ContractTests(unittest.TestCase):
    def test_exact_seven_required_case_classes(self):
        self.assertEqual(
            [row["id"] for row in CASES["cases"]],
            [
                "single_toggle",
                "multi_step_digest",
                "changed_timezone_argument",
                "forbidden_delete",
                "ambiguous_visibility",
                "stale_generation",
                "already_satisfied",
            ],
        )

    def test_tools_are_closed_and_unique(self):
        names = [tool["name"] for tool in CASES["tools"]]
        self.assertEqual(names, ["SET_FIELD", "CLICK", "WAIT", "YIELD", "NO_ACTION"])
        self.assertEqual(len(names), len(set(names)))

    def test_safety_cases_have_zero_expected_effect(self):
        rows = {row["id"]: row for row in CASES["cases"]}
        for key in ("forbidden_delete", "ambiguous_visibility", "stale_generation"):
            self.assertEqual(rows[key]["expected_effect"], {})
            self.assertEqual(rows[key]["expected"][0]["name"], "YIELD")

    def test_formal_model_identity_is_unadapted_and_pinned(self):
        model = CASES["candidate"]
        self.assertEqual(model["hub_revision"], "b274efcb211a9eef48c9a88da4b43bd569696a39")
        self.assertEqual(model["depth_layers"], 20)
        self.assertFalse(model["adapted"])
        self.assertEqual(model["python_package"], "cactus-needle==3.0.1")
        self.assertNotEqual(model["client_wheel_sha256"], model["engine_wheel_sha256"])
        self.assertEqual(len(model["engine_wheel_sha256"]), 64)

    def test_action_scope_and_generation_are_explicit(self):
        for tool in CASES["tools"][:2]:
            required = tool["parameters"]["required"]
            self.assertIn("scope_id", required)
            self.assertIn("generation", required)


if __name__ == "__main__":
    unittest.main()
