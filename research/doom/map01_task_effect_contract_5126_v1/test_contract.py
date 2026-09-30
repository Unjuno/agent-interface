import copy
import json
import tempfile
import unittest
from pathlib import Path
from audit import audit
from contract import classify
from oracle import oracle
from run import cases, effect, positive


class StrictLineageTests(unittest.TestCase):
    def check(self, row, expected):
        c, o = classify(row), oracle(row)
        self.assertEqual(c, o)
        self.assertEqual(c["task_effect"], expected)
        self.assertFalse(c["grants_input_authority"])
        self.assertFalse(c["grants_task_authority"])
        return c

    def test_canonical_positive(self):
        row = positive(); row["task_effects"] = [effect()]
        self.assertEqual(self.check(row, "TASK_EFFECT_SCOPED")["physical_actuation"], "PHYSICAL_ACTUATION_SCOPED")

    def test_each_top_level_id_rejects_blank_and_nonstring(self):
        for key in ("session_id", "plan_id", "actuation_id"):
            for bad in (" ", "x ", 7, None):
                row = positive(); row["task_effects"] = [effect()]; row[key] = bad
                with self.subTest(key=key, bad=bad): self.check(row, "UNRESOLVED_UNBOUND_OR_INVALID_EFFECT")

    def test_edge_ids_are_canonical_and_unique(self):
        for which in ("down", "up"):
            for bad in ("", "\t", "edge ", 1):
                row = positive(); row["task_effects"] = [effect()]
                row["physical"][which]["source_event_id"] = bad
                with self.subTest(which=which, bad=bad): self.check(row, "UNRESOLVED_UNBOUND_OR_INVALID_EFFECT")
        row = positive(); row["task_effects"] = [effect()]
        row["physical"]["up"]["source_event_id"] = row["physical"]["down"]["source_event_id"]
        self.check(row, "UNRESOLVED_UNBOUND_OR_INVALID_EFFECT")

    def test_effect_and_source_ids_are_canonical_unique(self):
        for key, bad in (("effect_id", " "), ("effect_id", "id "), ("effect_id", []),
                         ("source_event_id", "\n"), ("source_event_id", 0)):
            row = positive(); e = effect(); e[key] = bad; row["task_effects"] = [e]
            with self.subTest(key=key, bad=bad): self.check(row, "UNRESOLVED_UNBOUND_OR_INVALID_EFFECT")
        row = positive(); e = effect(); row["task_effects"] = [e, copy.deepcopy(e)]
        self.check(row, "UNRESOLVED_DUPLICATE_EFFECT")

    def test_state_feedback_is_not_task_effect(self):
        row = positive(); row["state_feedback"] = [{"session_id": "s1", "observed_ns": 1,
            "signal": "health", "before": 10, "after": 9}]
        out = self.check(row, "UNRESOLVED_NO_TASK_EFFECT")
        self.assertFalse(out["state_feedback"][0]["authority"])

    def test_foreign_plan_early_effect_and_scorer_taint_reject(self):
        mutations = (("plan_id", "other"), ("observed_ns", 109), ("scorer_independent", False),
                     ("controller_visible", True), ("kind", "HUD_HEALTH_CHANGE"))
        for key, value in mutations:
            row = positive(); e = effect(); e[key] = value; row["task_effects"] = [e]
            with self.subTest(key=key): self.check(row, "UNRESOLVED_UNBOUND_OR_INVALID_EFFECT")

    def test_raw_only_auditor_detects_whitespace_lineage_corruption(self):
        rows = []
        for case_id, raw, expected in cases():
            rows.append({"case_id": case_id, "raw": raw, "expected_task_effect": expected,
                         "candidate": classify(raw), "oracle": oracle(raw)})
        positive_row = next(row for row in rows if row["case_id"] == "valid_positive")
        positive_row["raw"]["session_id"] = " "
        document = {"schema": "map01-task-effect-contract-result-v2", "issue": 5126,
                    "input_authority": False, "live_calls": 0, "cases": rows}
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "mutated.json"
            path.write_text(json.dumps(document))
            result = audit(path)
        self.assertNotEqual(result["status"], "PASS_STRICT_LINEAGE_FINITE_CONTRACT")
        self.assertTrue(any(error.startswith("physical_raw_reconstruction:") for error in result["errors"]))


if __name__ == "__main__": unittest.main()
