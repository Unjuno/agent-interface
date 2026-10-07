import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "research" / "live_control"))
sys.path.insert(0, str(ROOT / "research" / "doom"))

from doom_typed_observation_v1 import build_action_snapshot
from observable_signal_guard_v2 import ObservableSignalGuard


def fixture():
    return json.loads((HERE / "fixture.json").read_text(encoding="utf-8"))


def contract():
    return {"format": "action-validity-contract-v1",
            "source": {"signals": {"health": {}, "ammo": {}}}}


def naive_a02_compose(source_event, current_event):
    floors = {"health": 90, "ammo": 1}
    outcomes = {}
    for name, floor in floors.items():
        source = source_event["signals"][name]
        guard = ObservableSignalGuard({
            "op": "observable_signal_guard", "guard_id": f"a02-{name}",
            "source_sequence": source["sequence"], "signal_id": name,
            "source_value": source["value"], "hard_minimum": floor,
            "max_source_age_ms": 30000,
            "on_soft_change": "preserve_existing_policy",
            "on_hard_change": "needs_decision", "on_unknown": "needs_decision",
        }, source, source["binding"])
        outcomes[name] = guard.evaluate(current_event["signals"][name])
    return outcomes


class EpochJoinTests(unittest.TestCase):
    def test_a02_control_preserves_individually_valid_but_split_epoch_signals(self):
        data = fixture()
        split = next(row["event"] for row in data["cases"]
                     if row["name"] == "signal_sequence_skew")
        outcomes = naive_a02_compose(data["source_event"], split)
        self.assertEqual(outcomes["health"]["status"], "UNCHANGED")
        self.assertEqual(outcomes["ammo"]["status"], "SOFT_CHANGED")
        self.assertFalse(any(row["requires_new_decision"] for row in outcomes.values()))

    def test_current_typed_snapshot_builder_rejects_sequence_skew(self):
        data = fixture()
        split = next(row["event"] for row in data["cases"]
                     if row["name"] == "signal_sequence_skew")
        with self.assertRaises(ValueError):
            build_action_snapshot(split, contract())

    def test_candidate_pair_decisions(self):
        from candidate import assess_pair

        data = fixture()
        for case in data["cases"]:
            with self.subTest(case=case["name"]):
                result = assess_pair(data["source_event"], case["event"])
                self.assertEqual(result["decision"], case["decision"])

    def test_candidate_fails_closed_on_malformed_source_frame(self):
        from candidate import assess_pair

        data = fixture()
        source = json.loads(json.dumps(data["source_event"]))
        source["signals"]["ammo"]["sequence"] += 1
        result = assess_pair(source, data["cases"][0]["event"])
        self.assertEqual(result["decision"], "replan")
        self.assertEqual(result["reason"], "source_typed_frame_invalid")


if __name__ == "__main__":
    unittest.main()
