import json
import sys
import tempfile
import unittest
from pathlib import Path
from threading import Lock

from checkpoint_candidate import PENDING, checkpoint

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "research/doom/scorer_checkpoint_tic_ack_t0_v1"))
from candidate import SUCCESS_STATUS, audit_refresh


class Executor:
    lock = Lock()
    closed = False
    active = None


class Owner:
    def call(self, name):
        return {"owned_keycodes": [], "owned_buttons": [],
                "active_lease_deadline_ns": None}


class State:
    def __init__(self, tic, values):
        self.tic, self.game_variables = tic, values


class Game:
    def __init__(self, before, after, state_tic, values, read_tic=None,
                 configured_variables=None):
        self.tics = [before, after, read_tic if read_tic is not None else after]
        self.state = State(state_tic, values)
        self.clock_reads = 0
        self.configured_variables = configured_variables or []

    def is_episode_finished(self):
        return False

    def get_episode_time(self):
        value = self.tics[min(self.clock_reads, len(self.tics) - 1)]
        self.clock_reads += 1
        return value

    def advance_action(self, frames, update):
        pass

    def get_state(self):
        return self.state

    def get_available_game_variables(self):
        return self.configured_variables


class CandidateTests(unittest.TestCase):
    def run_checkpoint(self, game):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "events.jsonl"
            variables = {"DEATHCOUNT": "death", "KILLCOUNT": "kill"}
            if not game.configured_variables:
                game.configured_variables = list(variables.values())
            receipt = checkpoint(game, Executor(), Owner(), variables, path, "test")
            row = json.loads(path.read_text().strip())
            return receipt, row

    def test_one_tic_ack_with_coherent_snapshot(self):
        receipt, row = self.run_checkpoint(Game(10, 11, 11, [0, 1]))
        self.assertEqual(receipt["status"], PENDING)
        self.assertEqual(row["values"], {"DEATHCOUNT": 0.0, "KILLCOUNT": 1.0})
        self.assertEqual(row["tic_after_read"], 11)
        self.assertFalse(row["grants_input_authority"])
        self.assertNotIn("values", receipt)

    def test_multi_tic_ack_matches_snapshot_and_is_accepted(self):
        receipt, row = self.run_checkpoint(Game(1, 11, 11, [0, 0]))
        self.assertEqual(receipt["status"], PENDING)
        self.assertEqual(row["tic_after"] - row["tic_before"], 10)
        self.assertEqual(row["state_tic"], row["tic_after"])

    def test_retained_async_spectator_counterexample_composes(self):
        raw_path = (REPO / "research/doom/scorer_async_spectator_59_t0_a01_20261004" /
                    "raw.json")
        raw = json.loads(raw_path.read_text(encoding="utf-8"))
        update = raw["update"]
        snapshot = raw["after_acknowledged_update"]
        old = audit_refresh({
            "status": SUCCESS_STATUS,
            "tic_before": update["episode_before"],
            "tic_after": update["episode_after"],
            "tic_after_read": snapshot["state_tic"],
        })
        self.assertFalse(old["qualified"])
        self.assertEqual(old["reason"], "tic_did_not_advance_exactly_one")

        receipt, row = self.run_checkpoint(Game(
            update["episode_before"], update["episode_after"],
            snapshot["state_tic"], snapshot["state_variables"]))
        self.assertEqual(receipt["status"], PENDING)
        self.assertEqual(row["tic_delta"], 10)
        self.assertEqual(row["state_tic"], 11)
        self.assertEqual(row["values"], {"DEATHCOUNT": 0.0, "KILLCOUNT": 0.0})

    def test_no_op_update_fails_closed(self):
        receipt, row = self.run_checkpoint(Game(7, 7, 7, [0, 0]))
        self.assertEqual(receipt["status"], "UNKNOWN")
        self.assertNotIn("values", row)

    def test_snapshot_mismatch_fails_closed(self):
        receipt, row = self.run_checkpoint(Game(1, 11, 10, [0, 0]))
        self.assertEqual(receipt["status"], "UNKNOWN")
        self.assertNotIn("values", row)

    def test_configured_variable_order_mismatch_fails_closed(self):
        game = Game(1, 11, 11, [0, 1], configured_variables=["kill", "death"])
        receipt, row = self.run_checkpoint(game)
        self.assertEqual(receipt["status"], "UNKNOWN")
        self.assertNotIn("values", row)

    def test_tic_drift_during_read_fails_closed(self):
        receipt, row = self.run_checkpoint(Game(1, 11, 11, [0, 0], read_tic=12))
        self.assertEqual(receipt["status"], "UNKNOWN")
        self.assertNotIn("values", row)


if __name__ == "__main__":
    unittest.main()
