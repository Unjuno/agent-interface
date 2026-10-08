import copy
import json
import unittest

from audit import validate
from protocol import bind_intent, expected_bound, make_rows, simulate_bound


class AuditTests(unittest.TestCase):
    def test_synthetic_raw_and_five_mutations(self):
        data = {"heldout": make_rows(4790127, "heldout", 64)}
        for row in data["heldout"]:
            row["expected_bound"] = expected_bound(row)
            row["expected_effect"] = simulate_bound(row["expected_bound"], row["state"])
        raw = {"arm": "adapter", "results": []}
        for row in data["heldout"]:
            text = json.dumps(row["intent"], sort_keys=True, separators=(",", ":"))
            raw["results"].append({"case_id": row["case_id"], "raw_text": text,
                                   "parsed": row["intent"], "parse_error": None,
                                   "bound": bind_intent(row["intent"], row["state"], row["requested_generation"]),
                                   "effect": simulate_bound(bind_intent(row["intent"], row["state"], row["requested_generation"]), row["state"]),
                                   "latency_ns": 100, "input_tokens": 20,
                                   "output_token_ids": list(range(7)), "output_tokens": 7})
        fit = {"rows": 32, "optimizer_steps": 16, "epochs": 1}
        self.assertTrue(validate(data, raw, fit, "adapter")["integrity"])
        mutations = []
        x = copy.deepcopy(raw); x["results"].pop(); mutations.append(x)
        x = copy.deepcopy(raw); x["results"].append(x["results"][-1]); mutations.append(x)
        x = copy.deepcopy(raw); x["results"][0]["raw_text"] = "{}"; mutations.append(x)
        x = copy.deepcopy(raw); x["results"][0]["bound"]["arguments"]["scope_id"] = "forged"; mutations.append(x)
        x = copy.deepcopy(raw); x["results"][0]["output_tokens"] = -1; mutations.append(x)
        self.assertEqual(sum(not validate(data, item, fit, "adapter")["integrity"] for item in mutations), 5)


if __name__ == "__main__":
    unittest.main()
