"""Synthetic construction checks for private reset and score receipts."""

import copy
import unittest
from pathlib import Path

from private_reset_audit import __file__ as audit_path
from private_reset_audit import (GUARD, geometry_receipt, score_receipt,
                                 reset_failure_receipt, reset_witness_receipt,
                                 verify_reset_witness)

MOD_SOURCE = Path(audit_path).resolve().parent / "mindustry_mod" / "main.js"


def snapshot():
    return {"tick": 100.0, "paused": True,
        "tiles": [{"x": x, "y": y, "block": "air", "team": 1,
                   "rotation": None, "floor": "stone", "overlay": "air"}
                  for y in range(48, 56) for x in range(136, 150)],
        "copper": 500, "core_x": 130, "core_y": 50, "source_item": "copper",
        "player_dead": False,
        "unit": {"x": 1000.0, "y": 900.0, "type": "mono", "plans": 0}}


def evaluation():
    return {"status": "VERIFIED", "contract_satisfied": True,
            "wrong_target": False, "collateral_tiles": [],
            "source_preserved": True, "core_preserved": True,
            "copper_delta": -1, "paused_idle_completion": True,
            "guard_tiles": 112,
            "scope": "one changed-geometry Mindustry placement; no delivery or route-completion claim"}


class PrivateResetAuditTests(unittest.TestCase):
    def test_candidate_mod_keeps_private_reset_and_b1_geometry_barriers(self):
        source = MOD_SOURCE.read_text(encoding="utf-8")
        self.assertIn('System.getProperty("agent.interface.benchmarkControlDir")', source)
        self.assertIn('phase==="awaitReset" && f("score-pass-"+taskEpoch+".receipt").exists()', source)
        self.assertIn('phase==="awaitReset" && f("score-fail-"+taskEpoch+".receipt").exists()', source)
        self.assertIn('phase==="awaitResetWitness" && f("reset-"+taskEpoch+".verified").exists()', source)
        self.assertIn('phase==="awaitResetWitness" && f("reset-"+taskEpoch+".fail").exists()', source)
        verified_gate = source.index('phase==="awaitResetWitness" && f("reset-"+taskEpoch+".verified").exists()')
        self.assertLess(verified_gate, source.index("taskEpoch++", verified_gate))
        self.assertLess(source.index("taskEpoch++", verified_gate),
                        source.index('f("ready-"+taskEpoch+".ack")', verified_gate))
        self.assertIn('if(taskEpoch===4){phase="awaitGeometry";', source)
        self.assertIn('phase==="awaitGeometry" && f("geometry-4.receipt").exists()', source)
        self.assertIn('f("ready-4.ack").writeString("verified A-to-B geometry ready")', source)
        self.assertNotIn('f("ready-4.ack").writeString("next task ready")', source)

    def test_exact_pre_task_projection_is_a_reset_witness(self):
        before = snapshot()
        after = copy.deepcopy(before)
        after["tick"] += 1
        report = verify_reset_witness(before, after)
        self.assertTrue(report["verified"])
        self.assertEqual(report["errors"], [])
        self.assertEqual(len(GUARD), 112)

    def test_target_mutation_and_resource_mismatch_refuse_witness(self):
        before = snapshot()
        after = copy.deepcopy(before)
        next(row for row in after["tiles"] if (row["x"], row["y"]) == (137, 52))["block"] = "conveyor"
        after["copper"] -= 1
        report = verify_reset_witness(before, after)
        self.assertFalse(report["verified"])
        self.assertIn("guard_projection_not_restored", report["errors"])
        self.assertIn("canonical_copper_not_restored", report["errors"])

    def test_pending_plan_or_running_game_refuses_witness(self):
        before = snapshot()
        after = copy.deepcopy(before)
        after["unit"]["plans"] = 1
        after["paused"] = False
        report = verify_reset_witness(before, after)
        self.assertFalse(report["verified"])
        self.assertIn("pending_build_plan_or_unit_projection", report["errors"])
        self.assertIn("paused_state_not_restored", report["errors"])

    def test_duplicate_or_missing_guard_tiles_refuse_witness(self):
        before = snapshot()
        malformed = copy.deepcopy(before)
        malformed["tiles"].pop()
        report = verify_reset_witness(before, malformed)
        self.assertFalse(report["verified"])
        self.assertIn("complete 112-tile guard projection required", report["errors"])

    def test_only_positive_independent_score_yields_private_reset_receipt(self):
        receipt = score_receipt("A3", evaluation())
        self.assertEqual(receipt["filename"], "score-pass-3.receipt")
        self.assertIn("private benchmark control", receipt["authority"])
        wrong_target = evaluation()
        wrong_target["wrong_target"] = True
        with self.assertRaisesRegex(ValueError, "positive task score"):
            score_receipt("B1", wrong_target)
        incomplete = evaluation()
        incomplete.pop("copper_delta")
        with self.assertRaisesRegex(ValueError, "exact independent"):
            score_receipt("B1", incomplete)

    def test_geometry_transition_receipt_requires_same_surface_and_changed_box(self):
        receipt = geometry_receipt(
            {"surface": 91, "geometry": [0, 24, 1280, 760]},
            {"surface": 91, "geometry": [0, 24, 1216, 760]})
        self.assertEqual(receipt["filename"], "geometry-4.receipt")
        with self.assertRaisesRegex(ValueError, "surface identity"):
            geometry_receipt(
                {"surface": 91, "geometry": [0, 24, 1280, 760]},
                {"surface": 92, "geometry": [0, 24, 1216, 760]})
        with self.assertRaisesRegex(ValueError, "must change"):
            geometry_receipt(
                {"surface": 91, "geometry": [0, 24, 1280, 760]},
                {"surface": 91, "geometry": [0, 24, 1280, 760]})

    def test_next_task_receipt_follows_only_verified_reset_audit(self):
        good = verify_reset_witness(snapshot(), snapshot())
        receipt = reset_witness_receipt("A2", good)
        self.assertEqual(receipt["filename"], "reset-2.verified")
        bad = {"verified": False, "errors": ["guard_projection_not_restored"],
               "authority": "private reset audit only; never controller-visible"}
        self.assertEqual(reset_failure_receipt("A2", bad)["filename"], "reset-2.fail")
        with self.assertRaisesRegex(ValueError, "positive exact reset witness"):
            reset_witness_receipt("A2", bad)


if __name__ == "__main__":
    unittest.main()
