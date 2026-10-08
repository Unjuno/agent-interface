import json
import math
import unittest
from pathlib import Path

import candidate_snapshot

ROOT = Path(__file__).resolve().parent


def qualify(**kwargs):
    implementation = getattr(candidate_snapshot, "qualify_state_snapshot", None)
    if not callable(implementation):
        raise AssertionError("candidate snapshot qualifier is not implemented")
    return implementation(**kwargs)


class SnapshotQualificationTests(unittest.TestCase):
    def test_retained_async_spectator_interval_accepts_coherent_multi_tic_snapshot(self):
        raw = json.loads((ROOT / "raw.json").read_text())
        before = raw["update"]["episode_before"]
        after = raw["update"]["episode_after"]
        sample = raw["after_acknowledged_update"]
        self.assertEqual(after - before, 10)
        record = qualify(tic_before=before, tic_after=after,
                         state_tic=sample["state_tic"],
                         game_variables=sample["state_variables"],
                         variable_names=["DEATHCOUNT", "KILLCOUNT"])
        self.assertEqual(record["controller_reply"]["status"],
                         "REFRESH_RETURNED_RUNTIME_QUALIFICATION_PENDING")
        self.assertEqual(record["record"]["tic_delta"], 10)
        self.assertEqual(record["record"]["state_tic"], 11)
        self.assertEqual(record["record"]["values"],
                         {"DEATHCOUNT": 0.0, "KILLCOUNT": 0.0})
        self.assertFalse(record["record"]["grants_input_authority"])

    def test_no_new_snapshot_fails_closed(self):
        record = qualify(tic_before=7, tic_after=7, state_tic=7,
                         game_variables=[0.0, 0.0],
                         variable_names=["DEATHCOUNT", "KILLCOUNT"])
        self.assertEqual(record["controller_reply"]["status"], "UNKNOWN")
        self.assertEqual(record["record"]["reason"], "snapshot_not_newer")

    def test_snapshot_endpoint_disagreement_fails_closed(self):
        record = qualify(tic_before=7, tic_after=9, state_tic=8,
                         game_variables=[0.0, 0.0],
                         variable_names=["DEATHCOUNT", "KILLCOUNT"])
        self.assertEqual(record["controller_reply"]["status"], "UNKNOWN")
        self.assertEqual(record["record"]["reason"], "snapshot_tic_disagrees_with_endpoint")

    def test_wrong_variable_count_fails_closed(self):
        record = qualify(tic_before=7, tic_after=9, state_tic=9,
                         game_variables=[0.0],
                         variable_names=["DEATHCOUNT", "KILLCOUNT"])
        self.assertEqual(record["controller_reply"]["status"], "UNKNOWN")
        self.assertEqual(record["record"]["reason"], "variable_count_mismatch")

    def test_nonfinite_score_value_fails_closed(self):
        record = qualify(tic_before=7, tic_after=9, state_tic=9,
                         game_variables=[0.0, math.nan],
                         variable_names=["DEATHCOUNT", "KILLCOUNT"])
        self.assertEqual(record["controller_reply"]["status"], "UNKNOWN")
        self.assertEqual(record["record"]["reason"], "invalid_game_variable")

    def test_boolean_tic_fails_closed(self):
        record = qualify(tic_before=True, tic_after=9, state_tic=9,
                         game_variables=[0.0], variable_names=["SCORE"])
        self.assertEqual(record["record"]["reason"], "invalid_tic")

    def test_duplicate_variable_names_fail_closed(self):
        record = qualify(tic_before=7, tic_after=9, state_tic=9,
                         game_variables=[0.0, 1.0], variable_names=["SCORE", "SCORE"])
        self.assertEqual(record["record"]["reason"], "duplicate_variable_name")

    def test_boolean_game_variable_fails_closed(self):
        record = qualify(tic_before=7, tic_after=9, state_tic=9,
                         game_variables=[0.0, True], variable_names=["SCORE", "KILLS"])
        self.assertEqual(record["record"]["reason"], "invalid_game_variable")


if __name__ == "__main__":
    unittest.main()
