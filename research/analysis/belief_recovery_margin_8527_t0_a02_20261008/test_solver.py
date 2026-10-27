import unittest
import json
from pathlib import Path

from candidate import classify, run


FIXTURE = json.loads((Path(__file__).parent / "input.json").read_text(encoding="utf-8"))


def problem(states, observations, transitions, marker, unsafe=(), initial=None, complete=True,
            generation_current=True, marker_verified=True):
    return {
        "states": list(states),
        "observations": observations,
        "transitions": transitions,
        "marker": list(marker),
        "unsafe": list(unsafe),
        "initial_belief": list(initial if initial is not None else states),
        "model_complete": complete,
        "generation_current": generation_current,
        "marker_verified": marker_verified,
        "authorized_actions": sorted({action for row in transitions.values() for action in row}),
    }


class BeliefRecoveryConstructionTests(unittest.TestCase):
    def test_joint_belief_is_not_statewise_union_of_opposite_recoveries(self):
        p = problem(
            ["L", "R", "ML", "MR", "BAD"],
            {"L": "same", "R": "same", "ML": "left-done", "MR": "right-done", "BAD": "bad"},
            {
                "L": {"LEFT": ["ML"], "RIGHT": ["BAD"]},
                "R": {"LEFT": ["BAD"], "RIGHT": ["MR"]},
                "ML": {}, "MR": {}, "BAD": {},
            },
            ["ML", "MR"], ["BAD"], ["L", "R"],
        )
        joint = classify(p, 2)
        left = classify({**p, "initial_belief": ["L"]}, 2)
        right = classify({**p, "initial_belief": ["R"]}, 2)
        self.assertEqual(joint["status"], "NOT_RECOVERABLE")
        self.assertEqual(left["status"], "RECOVERABLE")
        self.assertEqual(right["status"], "RECOVERABLE")

    def test_safe_observation_split_recovers_only_with_two_steps(self):
        p = problem(
            ["L", "R", "L1", "R1", "ML", "MR", "BAD"],
            {"L": "same", "R": "same", "L1": "left-cue", "R1": "right-cue",
             "ML": "left-done", "MR": "right-done", "BAD": "bad"},
            {
                "L": {"SCAN": ["L1"]}, "R": {"SCAN": ["R1"]},
                "L1": {"LEFT": ["ML"], "RIGHT": ["BAD"]},
                "R1": {"LEFT": ["BAD"], "RIGHT": ["MR"]},
                "ML": {}, "MR": {}, "BAD": {},
            },
            ["ML", "MR"], ["BAD"], ["L", "R"],
        )
        self.assertEqual(classify(p, 2)["status"], "RECOVERABLE")
        self.assertEqual(classify(p, 1)["status"], "NOT_RECOVERABLE")

    def test_exact_deadline_boundary_is_inclusive(self):
        p = problem(
            ["S0", "S1", "M"], {"S0": "a", "S1": "b", "M": "m"},
            {"S0": {"GO": ["S1"]}, "S1": {"GO": ["M"]}, "M": {}}, ["M"],
            initial=["S0"],
        )
        self.assertEqual(classify(p, 2)["minimum_steps"], 2)
        self.assertEqual(classify(p, 1)["status"], "NOT_RECOVERABLE")

    def test_missing_transition_mass_is_unknown_not_safe(self):
        p = problem(["S", "M"], {"S": "s", "M": "m"}, {"S": {"GO": ["M"]}, "M": {}},
                    ["M"], initial=["S"], complete=False)
        self.assertEqual(classify(p, 2)["status"], "UNKNOWN")

    def test_stale_generation_and_unverified_marker_are_unknown(self):
        base = problem(["S", "M"], {"S": "s", "M": "m"},
                       {"S": {"GO": ["M"]}, "M": {}}, ["M"], initial=["S"])
        self.assertEqual(classify({**base, "generation_current": False}, 1)["status"], "UNKNOWN")
        self.assertEqual(classify({**base, "marker_verified": False}, 1)["status"], "UNKNOWN")

    def test_frozen_corpus_has_expected_boundary_labels(self):
        raw = run(FIXTURE)
        by_key = {(r["case_id"], r["horizon"]): r for r in raw["rows"]}
        self.assertEqual(len(by_key), 40)
        self.assertEqual(by_key[("fully-observed", 1)]["minimum_steps"], 1)
        self.assertEqual(by_key[("aliased-opposite-actions", 3)]["status"], "NOT_RECOVERABLE")
        self.assertEqual(by_key[("safe-information-gathering", 2)]["minimum_steps"], 2)
        self.assertEqual(by_key[("safe-information-gathering", 1)]["status"], "NOT_RECOVERABLE")
        self.assertEqual(by_key[("exact-horizon-alternate-path", 2)]["margin"], 0)
        self.assertEqual(by_key[("omitted-transition-mass", 3)]["status"], "UNKNOWN")
        self.assertEqual(by_key[("stale-observation-generation", 3)]["status"], "UNKNOWN")
        self.assertEqual(by_key[("unverified-marker", 3)]["status"], "UNKNOWN")
        self.assertEqual(by_key[("missing-transition", 3)]["status"], "UNKNOWN")
        self.assertEqual(
            [x["result"]["status"] for x in raw["singleton_controls"]],
            ["RECOVERABLE", "RECOVERABLE"],
        )


if __name__ == "__main__":
    unittest.main()
