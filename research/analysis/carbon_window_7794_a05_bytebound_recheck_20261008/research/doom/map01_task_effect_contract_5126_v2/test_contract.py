import copy
import json
import tempfile
import unittest
from pathlib import Path
from audit import audit
from contract import classify
from oracle import oracle
from run import INPUT, INPUT_SHA256


def positive():
    source = json.loads(INPUT.read_text())
    row = next(r["raw"] for r in source["cases"] if r["case_id"] == "valid_positive")
    return copy.deepcopy(row)


class CrossPlaneIdentityTests(unittest.TestCase):
    def assert_classifiers(self, row, expected):
        candidate, reference = classify(row), oracle(row)
        self.assertEqual(candidate, reference)
        self.assertEqual(candidate["task_effect"], expected)
        self.assertFalse(candidate["grants_input_authority"])
        self.assertFalse(candidate["grants_task_authority"])
        return candidate

    def test_input_corpus_is_frozen(self):
        import hashlib
        self.assertEqual(hashlib.sha256(INPUT.read_bytes()).hexdigest(), INPUT_SHA256)

    def test_disjoint_source_namespaces_retain_positive(self):
        self.assertEqual(self.assert_classifiers(positive(), "TASK_EFFECT_SCOPED")["physical_actuation"],
                         "PHYSICAL_ACTUATION_SCOPED")

    def test_scorer_event_cannot_reuse_either_physical_edge_identity(self):
        for edge in ("down", "up"):
            row = positive()
            row["task_effects"][0]["source_event_id"] = row["physical"][edge]["source_event_id"]
            with self.subTest(edge=edge):
                self.assert_classifiers(row, "UNRESOLVED_DUPLICATE_SOURCE_EVENT")

    def test_physical_edge_ids_must_be_distinct(self):
        row = positive()
        row["physical"]["up"]["source_event_id"] = row["physical"]["down"]["source_event_id"]
        out = self.assert_classifiers(row, "UNRESOLVED_UNBOUND_OR_INVALID_EFFECT")
        self.assertEqual(out["physical_actuation"], "UNRESOLVED")

    def test_raw_only_auditor_detects_postclassification_cross_plane_collision(self):
        frozen = json.loads(INPUT.read_text())
        rows = []
        for old in frozen["cases"]:
            raw = copy.deepcopy(old["raw"])
            rows.append({"case_id": old["case_id"], "raw": raw,
                         "expected_task_effect": old["expected_task_effect"],
                         "candidate": classify(raw), "oracle": oracle(raw)})
        target = next(r for r in rows if r["case_id"] == "valid_positive")
        target["raw"]["task_effects"][0]["source_event_id"] = target["raw"]["physical"]["down"]["source_event_id"]
        doc = {"schema": "map01-task-effect-contract-result-v3", "issue": 5126,
               "input_corpus_sha256": INPUT_SHA256, "input_authority": False, "live_calls": 0, "cases": rows}
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "mutated.json"
            path.write_text(json.dumps(doc))
            result = audit(path)
        self.assertNotEqual(result["status"], "PASS_CROSS_PLANE_SOURCE_ID_GATE")
        self.assertTrue(any(error.endswith("valid_positive") for error in result["errors"]))


if __name__ == "__main__": unittest.main()
