import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


PACKAGE = Path(__file__).resolve().parents[1]
CANDIDATE = PACKAGE / "candidate" / "candidate.py"


class CandidatePacketContractTests(unittest.TestCase):
    def run_candidate(self, public_rows):
        with tempfile.TemporaryDirectory() as tmp:
            input_path = Path(tmp) / "public.json"
            output_path = Path(tmp) / "candidate.json"
            input_path.write_text(json.dumps({"rows": public_rows}, sort_keys=True))
            result = subprocess.run(
                [sys.executable, str(CANDIDATE), "--input", str(input_path), "--output", str(output_path)],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(0, result.returncode, result.stderr)
            return json.loads(output_path.read_text())

    def test_identical_public_views_with_different_hidden_truth_do_not_get_a_guessed_target(self):
        public_view = {
            "view": {"window": "task-board", "visible_checkpoint": "row-blue"},
            "cue": None,
            "current_epoch": 4,
            "view_epoch": 4,
            "window_matches_task": True,
            "emergency_release_required": False,
        }

        raw = self.run_candidate([public_view, dict(public_view)])

        self.assertEqual("human-return-oracle-blindness-candidate-v1", raw["schema"])
        self.assertEqual(raw["packets"][0], raw["packets"][1])
        self.assertEqual(
            {"status": "UNKNOWN", "cue": None, "target": None, "authority": "NONE", "release_required": False},
            raw["packets"][0],
        )

    def test_only_a_fresh_user_cue_is_surfaced_as_context_not_as_an_action(self):
        public_view = {
            "view": {"window": "task-board", "visible_checkpoint": "row-blue"},
            "cue": {"text": "Resume at the blue row", "origin": "USER", "epoch": 4},
            "current_epoch": 4,
            "view_epoch": 4,
            "window_matches_task": True,
            "emergency_release_required": False,
        }

        raw = self.run_candidate([public_view])

        self.assertEqual(
            {"status": "CUE_AVAILABLE", "cue": "Resume at the blue row", "target": None, "authority": "NONE", "release_required": False},
            raw["packets"][0],
        )

    def test_stale_or_agent_authored_cues_and_wrong_window_never_become_targets(self):
        base = {
            "view": {"window": "task-board", "visible_checkpoint": "row-blue"},
            "current_epoch": 4,
            "view_epoch": 4,
            "window_matches_task": True,
            "emergency_release_required": False,
        }
        stale = dict(base, cue={"text": "old cue", "origin": "USER", "epoch": 3})
        agent_authored = dict(base, cue={"text": "agent guess", "origin": "AGENT", "epoch": 4})
        wrong_window = dict(base, cue=None, window_matches_task=False)

        raw = self.run_candidate([stale, agent_authored, wrong_window])

        self.assertEqual(["UNKNOWN", "UNKNOWN", "UNKNOWN"], [row["status"] for row in raw["packets"]])
        self.assertTrue(all(row["target"] is None for row in raw["packets"]))
        self.assertTrue(all(row["cue"] is None for row in raw["packets"]))

    def test_offered_but_unused_cue_stays_unknown_and_emergency_release_is_preserved(self):
        base = {
            "view": {"window": "task-board", "visible_checkpoint": "row-blue"},
            "cue": None,
            "current_epoch": 4,
            "view_epoch": 4,
            "window_matches_task": True,
        }
        unused_offer = dict(base, cue_offer_accepted=True, emergency_release_required=False)
        emergency = dict(base, cue_offer_accepted=False, emergency_release_required=True)

        raw = self.run_candidate([unused_offer, emergency])

        self.assertEqual(["UNKNOWN", "UNKNOWN"], [row["status"] for row in raw["packets"]])
        self.assertEqual([False, True], [row["release_required"] for row in raw["packets"]])
        self.assertTrue(all(row["target"] is None for row in raw["packets"]))

    def test_unrecognized_truth_like_fields_are_not_echoed_or_used_to_guess(self):
        public_view = {
            "view": {"window": "task-board", "visible_checkpoint": "row-blue"},
            "cue": None,
            "current_epoch": 4,
            "view_epoch": 4,
            "window_matches_task": True,
            "emergency_release_required": False,
            "pending_step_code": "hidden-target-canary-7f3a",
        }

        raw = self.run_candidate([public_view])

        self.assertEqual(
            {"status": "UNKNOWN", "cue": None, "target": None, "authority": "NONE", "release_required": False},
            raw["packets"][0],
        )
        self.assertNotIn("hidden-target-canary-7f3a", json.dumps(raw, sort_keys=True))


if __name__ == "__main__":
    unittest.main()
