import copy
import json
import unittest
from pathlib import Path
from repair_v2.test_teardown_audit import regression_cases as previous_cases
from .json_witness_audit import audit

HERE = Path(__file__).resolve().parent.parent


def regression_cases(raw):
    yield from previous_cases(raw)
    for name, kind, index, field, value in (
        ("review_appended_bool_as_int", "appended", 1, "verified", 1),
        ("review_final_cancel_bool_as_int", "final", 6, "verified", 1),
        ("appended_bool_as_float", "appended", 1, "verified", 1.0),
        ("appended_two_key_bool_as_int", "appended", 5, "verified", 1),
        ("appended_lease_int_as_float", "appended", 1, "valid_until_ns", float(raw["cases"][1]["receipt"]["valid_until_ns"])),
        ("final_two_key_bool_as_int", "final", 4, "verified", 1),
        ("final_lease_int_as_float", "final", 1, "valid_until_ns", float(raw["cases"][1]["receipt"]["valid_until_ns"])),
    ):
        item = copy.deepcopy(raw)
        row = item["cases"][index]["owner_rows_appended"][0] if kind == "appended" else item["owner_snapshots_final"][index]
        row[field] = value
        # These are real parsed JSON values; no tuple/custom-object API fixtures.
        yield name, json.loads(json.dumps(item)), True
    item = copy.deepcopy(raw)
    for case in item["cases"]:
        if case["event"] == "teardown":
            case["receipt"] = dict(reversed(list(case["receipt"].items())))
    yield "object_key_order_is_irrelevant", item, False


class JsonWitnessTests(unittest.TestCase):
    def test_prior_controls_and_json_type_aliases(self):
        raw = json.loads((HERE / "retained/raw.json").read_text(encoding="utf-8"))
        rows = list(regression_cases(raw))
        self.assertEqual(len(rows), 38)
        self.assertEqual(len({name for name, _, _ in rows}), 38)
        for name, item, invalid in rows:
            with self.subTest(case=name):
                self.assertEqual(bool(audit(item)), invalid)


if __name__ == "__main__":
    unittest.main()
