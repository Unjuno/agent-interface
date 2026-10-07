"""V4 batch and InputOwner v12 physical-edge composition contract."""
import unittest

from .composition import run_composition


class V4V12CompositionTests(unittest.TestCase):
    def test_two_key_batch_retains_edges_and_exposes_inter_release_sampling(self):
        result = run_composition()
        rows = result["events"]
        admissions = [row for row in rows if row.get("event") == "input_admission"]
        releases = [row for row in rows if row.get("event") == "input_release_transition"]

        self.assertEqual([row["key"] for row in admissions], ["F8", "SPACE"])
        self.assertEqual([row["key"] for row in releases], ["SPACE", "F8"])
        self.assertEqual(
            [row["physical_key_measurement"]["classification"] for row in admissions],
            ["CONFIRMED_PHYSICAL_DOWN", "CONFIRMED_PHYSICAL_DOWN"],
        )
        self.assertEqual(
            [row["physical_key_measurement"]["classification"] for row in releases],
            ["CONFIRMED_PHYSICAL_UP", "CONFIRMED_PHYSICAL_UP"],
        )
        down_ids = {
            row["key"]: row["physical_key_measurement"]["actuation_id"]
            for row in admissions
        }
        self.assertEqual(
            {row["key"]: row["physical_key_measurement"]["actuation_id"]
             for row in releases},
            down_ids,
        )
        self.assertTrue(all(row["owner_transition_verified"] for row in releases))
        self.assertTrue(all(row["grants_input_authority"] is False for row in releases))
        self.assertEqual(result["physical_keys_after"], [])
        self.assertEqual(result["backend_held_after"], [])

        operations = result["operations"]
        up_positions = [i for i, item in enumerate(operations)
                        if item["operation"] == "key-up"]
        self.assertEqual(len(up_positions), 2)
        between = operations[up_positions[0] + 1:up_positions[1]]
        self.assertEqual(
            sum(item["operation"] == "keymap-sample" for item in between), 2
        )
        self.assertGreaterEqual(
            releases[1]["release_call_started_ns"]
            - releases[0]["release_call_returned_ns"],
            0,
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
