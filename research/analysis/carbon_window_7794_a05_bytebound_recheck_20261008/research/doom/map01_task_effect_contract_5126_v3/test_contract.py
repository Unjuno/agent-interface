import copy
import json
import tempfile
import unittest
from pathlib import Path
from audit import audit
from contract import classify
from oracle import oracle
from run import INPUT, make_rows


class TaxonomyRepairTests(unittest.TestCase):
    def test_candidate_and_oracle_agree_on_all_retained_cases(self):
        _, rows = make_rows()
        self.assertEqual(len(rows), 13)
        self.assertTrue(all(row["candidate"] == row["oracle"] for row in rows))
        self.assertTrue(all(row["candidate"]["grants_input_authority"] is False for row in rows))
        self.assertTrue(all(row["candidate"]["grants_task_authority"] is False for row in rows))

    def test_cross_plane_collision_has_specific_refusal(self):
        rows = json.loads(INPUT.read_text())["cases"]
        row = copy.deepcopy(next(item["raw"] for item in rows if item["case_id"] == "valid_positive"))
        for edge in ("down", "up"):
            mutated = copy.deepcopy(row)
            mutated["task_effects"][0]["source_event_id"] = mutated["physical"][edge]["source_event_id"]
            with self.subTest(edge=edge):
                self.assertEqual(classify(mutated), oracle(mutated))
                self.assertEqual(classify(mutated)["task_effect"], "UNRESOLVED_DUPLICATE_SOURCE_EVENT")

    def test_same_plane_duplicate_retains_duplicate_effect_refusal(self):
        row = copy.deepcopy(next(item["raw"] for item in json.loads(INPUT.read_text())["cases"]
                                 if item["case_id"] == "valid_positive"))
        row["task_effects"].append(copy.deepcopy(row["task_effects"][0]))
        self.assertEqual(classify(row), oracle(row))
        self.assertEqual(classify(row)["task_effect"], "UNRESOLVED_DUPLICATE_EFFECT")

    def test_physical_down_and_up_ids_must_be_distinct(self):
        row = copy.deepcopy(next(item["raw"] for item in json.loads(INPUT.read_text())["cases"]
                                 if item["case_id"] == "valid_positive"))
        row["physical"]["up"]["source_event_id"] = row["physical"]["down"]["source_event_id"]
        self.assertEqual(classify(row), oracle(row))
        self.assertEqual(classify(row)["physical_actuation"], "UNRESOLVED")

    def test_raw_only_auditor_detects_postclassification_collision(self):
        _, rows = make_rows()
        target = next(row for row in rows if row["case_id"] == "valid_positive")
        target["raw"]["task_effects"][0]["source_event_id"] = target["raw"]["physical"]["down"]["source_event_id"]
        document = {"schema": "map01-task-effect-contract-result-v4",
                    "allocation": "MAP01-TASK-EFFECT-LINEAGE-5126-20260928-03", "issue": 5126,
                    "input_corpus_sha256": "536de27a25cdc7b9936235dc1ef900cf174f2acbf16239a696474ede5f69fa9f",
                    "input_authority": False, "live_calls": 0, "cases": rows}
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "mutated.json"
            path.write_text(json.dumps(document))
            result = audit(path)
        self.assertEqual(result["status"], "FAIL_CROSS_PLANE_IDENTITY_CONTRACT")
        self.assertTrue(any(error.endswith("valid_positive") for error in result["errors"]))


if __name__ == "__main__": unittest.main()
