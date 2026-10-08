import copy
import json
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from presenter import Custodian, make_packets, synthetic_scores


class RouteBlindT0Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = json.loads((HERE / "fixture.json").read_text(encoding="utf-8"))

    def test_presenter_is_reproducible_and_route_blind(self):
        a, escrow_a = make_packets(self.fixture, 7436001)
        b, escrow_b = make_packets(self.fixture, 7436001)
        c, _ = make_packets(self.fixture, 7436002)
        self.assertEqual(a, b)
        self.assertEqual(escrow_a, escrow_b)
        self.assertNotEqual(a["order"], c["order"])
        serialized = json.dumps(a, sort_keys=True)
        for value in ("ROUTE_ALPHA_EXPECTED_WINNER", "ROUTE_BETA_BASELINE", "CANDIDATE_FAST_ROUTE_ALPHA", "BRANCH_GUARDED_ALPHA", "PREDICTED_WINNER_ALPHA"):
            self.assertNotIn(value, serialized)
        self.assertEqual(len(a["packets"]), 6)

    def test_commit_required_before_reveal_and_tamper_fails(self):
        packets, escrow = make_packets(self.fixture, 7436001)
        custodian = Custodian(escrow)
        with self.assertRaises(PermissionError):
            custodian.reveal()
        scores = synthetic_scores(packets)
        pointers = {p["episode_id"]: p["evidence_pointer"] for p in packets["packets"]}
        commit = custodian.commit_scores(scores, packets["order"], pointers)
        self.assertEqual(commit["count"], 6)
        self.assertEqual(custodian.reveal(scores), escrow)
        tampered = copy.deepcopy(scores)
        tampered[0]["score"] = "uncertain" if scores[0]["score"] != "uncertain" else "useful"
        with self.assertRaises(ValueError):
            custodian.reveal(tampered)

    def test_missing_or_duplicate_or_wrong_pointer_score_is_refused(self):
        packets, escrow = make_packets(self.fixture, 7436001)
        pointers = {p["episode_id"]: p["evidence_pointer"] for p in packets["packets"]}
        scores = synthetic_scores(packets)
        with self.assertRaises(ValueError):
            Custodian(escrow).commit_scores(scores[:-1], packets["order"], pointers)
        duplicate = copy.deepcopy(scores)
        duplicate[-1]["episode_id"] = duplicate[0]["episode_id"]
        with self.assertRaises(ValueError):
            Custodian(escrow).commit_scores(duplicate, packets["order"], pointers)
        wrong = copy.deepcopy(scores)
        wrong[0]["evidence_pointer"] = "evidence:wrong"
        with self.assertRaises(ValueError):
            Custodian(escrow).commit_scores(wrong, packets["order"], pointers)

    def test_only_required_evidence_and_rubric_are_presented(self):
        packets, escrow = make_packets(self.fixture, 7436001)
        self.assertTrue(escrow)
        for packet in packets["packets"]:
            self.assertEqual(set(packet), {"episode_id", "stratum", "evidence", "rubric", "evidence_pointer"})
            self.assertEqual(packet["rubric"], self.fixture["rubric"])
            self.assertNotIn("route", packet)

    def test_raw_canaries_are_in_actual_source_paths_and_filenames(self):
        for row in self.fixture["cases"]:
            path = HERE / row["artifact_path"]
            self.assertTrue(path.is_file())
            self.assertIn(row["route"], str(path))
            self.assertIn(row["filename"], path.name)
            raw = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(raw["evidence"], row["evidence"])


if __name__ == "__main__":
    unittest.main()
