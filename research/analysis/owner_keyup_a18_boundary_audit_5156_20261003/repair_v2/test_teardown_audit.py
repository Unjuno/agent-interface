import copy
import json
import unittest
from pathlib import Path
from mutations import cases as original_cases
from .teardown_audit import audit

HERE = Path(__file__).resolve().parent.parent


def regression_cases(raw):
    yield from original_cases(raw)
    for index in (1, 5):
        for field in ("owner_id", "intent_token", "verified_ns"):
            item = copy.deepcopy(raw)
            witness = item["cases"][index]["owner_rows_appended"][0]
            witness[field] = {"owner_id": "f" * 32,
                              "intent_token": "foreign-intent",
                              "verified_ns": witness["verified_ns"] + 1}[field]
            yield f"teardown_{index}_appended_{field}", item, True
    for index in (1, 5, 8):
        for variant in ("before_call", "after_call", "within_call_disagrees"):
            item = copy.deepcopy(raw)
            receipt = item["cases"][index]["receipt"]
            receipt["verified_ns"] = {
                "before_call": receipt["release_call_started_ns"] - 1,
                "after_call": receipt["release_call_returned_ns"] + 1,
                "within_call_disagrees": receipt["verified_ns"] + 1,
            }[variant]
            yield f"teardown_{index}_{variant}", item, True
    item = copy.deepcopy(raw)
    item["cases"][1]["owner_rows_appended"] = []
    yield "teardown_missing_appended", item, True
    item = copy.deepcopy(raw)
    item["owner_snapshots_final"].append(copy.deepcopy(item["cases"][1]["owner_rows_appended"][0]))
    yield "teardown_duplicate_final", item, True
    item = copy.deepcopy(raw)
    item["owner_snapshots_final"][1]["verified_ns"] += 1
    yield "teardown_final_disagrees", item, True
    item = copy.deepcopy(raw)
    item["cases"][1]["owner_rows_appended"][0]["unrecorded_field"] = "extra"
    yield "teardown_appended_extra_field", item, True


class TeardownTests(unittest.TestCase):
    def test_retained_control_and_corruption_matrix(self):
        raw = json.loads((HERE / "retained/raw.json").read_text(encoding="utf-8"))
        rows = list(regression_cases(raw))
        self.assertEqual(len(rows), 30)
        self.assertEqual(len({name for name, _, _ in rows}), 30)
        for name, item, invalid in rows:
            with self.subTest(case=name):
                self.assertEqual(bool(audit(item)), invalid)


if __name__ == "__main__":
    unittest.main()
