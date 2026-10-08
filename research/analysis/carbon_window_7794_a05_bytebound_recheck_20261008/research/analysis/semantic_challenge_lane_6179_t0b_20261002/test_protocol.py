import copy
import json
import unittest

from auditor import audit
from candidate import build_raw


class BrokerBoundaryTests(unittest.TestCase):
    def test_full_grid_and_independent_audit(self):
        raw = build_raw()
        self.assertEqual(len(raw["runs"]), 18)
        self.assertEqual(audit(raw), [])
        self.assertEqual(audit(json.loads(json.dumps(raw))), [])

    def test_all_attacks_are_submitted_and_rejected(self):
        raw = build_raw()
        for row in raw["runs"]:
            attempts = row["attack_results"]["attempts"]
            self.assertEqual([x["attack"] for x in attempts],
                             ["forged_capability", "old_generation_replay", "challenge_as_ordinary"])
            self.assertTrue(all(x["accepted"] is False for x in attempts))
            self.assertEqual(row["attack_results"]["ordinary_reducer_accepts"], 0)
            self.assertEqual(row["attack_results"]["publisher_events"], 0)
            self.assertEqual(row["attack_results"]["actuator_effects"], 0)

    def test_in_path_blocks_each_semantic_mutant_before_release(self):
        raw = build_raw()
        rows = {r["condition"]: r for r in raw["runs"] if r["route"] == "in_path_challenge"}
        for condition in ("stuck_pass", "stale_cache", "parser_omission", "skip_mandatory"):
            self.assertTrue(rows[condition]["detected_before_release"], condition)
            self.assertFalse(rows[condition]["ordinary_verdict_released"], condition)
        for condition in ("healthy", "healthy_slow"):
            self.assertFalse(rows[condition]["detected_before_release"], condition)
            self.assertTrue(rows[condition]["ordinary_verdict_released"], condition)

    def test_baselines_show_semantic_fault_escape(self):
        raw = build_raw()
        for route in ("heartbeat_only", "detached_startup_probe"):
            rows = [r for r in raw["runs"] if r["route"] == route]
            self.assertTrue(all(r["ordinary_verdict_released"] for r in rows))
            self.assertTrue(all(not r["detected_before_release"] for r in rows))

    def test_auditor_rejects_forged_acceptance_and_false_detection(self):
        raw = build_raw()
        changed = copy.deepcopy(raw)
        changed["runs"][0]["attack_results"]["attempts"][0]["accepted"] = True
        self.assertTrue(audit(changed))

        changed = copy.deepcopy(raw)
        row = next(r for r in changed["runs"] if r["route"] == "in_path_challenge"
                   and r["condition"] == "healthy")
        row["ordinary_verdict_released"] = False
        self.assertTrue(audit(changed))

    def test_auditor_rejects_fixture_and_submitted_envelope_tampering(self):
        mutations = [
            ("vectors", lambda x: x[0].update(target="task-forged")),
            ("nonce", lambda x: x["runs"][0]["attack_results"].update(nonce="nonce-forged")),
            ("envelope", lambda x: x["runs"][0]["attack_results"]["attempts"][0]["submitted"].update(capability="fixture-capability-6179-t0b")),
            ("drop-attack", lambda x: x["runs"][0]["attack_results"]["attempts"].pop()),
            ("effect-counter", lambda x: x["runs"][0]["attack_results"].update(publisher_events=1)),
            ("grid-order", lambda x: x["runs"].reverse()),
        ]
        for name, mutate in mutations:
            with self.subTest(name=name):
                changed = copy.deepcopy(build_raw())
                if name == "vectors":
                    mutate(changed["vectors"])
                elif name == "grid-order":
                    mutate(changed)
                else:
                    mutate(changed)
                self.assertTrue(audit(changed), name)


if __name__ == "__main__":
    unittest.main(verbosity=2)
