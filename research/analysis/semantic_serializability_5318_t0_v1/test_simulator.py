import unittest
import simulator


class SimulatorConstructionTests(unittest.TestCase):
    def test_fixture_is_six_scenarios_and_five_policies(self):
        self.assertEqual(len(simulator.scenarios()), 6)
        self.assertEqual(len(simulator.POLICIES), 5)

    def test_trusted_commutative_adds_are_both_applied(self):
        case = next(c for c in simulator.scenarios() if c["id"] == "commuting_add")
        decision, final, committed = simulator.decide(case, "SEMANTIC_SERIALIZABILITY")
        self.assertEqual((decision, final["x"], committed), ("PARALLEL", 3, ["p1", "p2"]))

    def test_write_skew_cycle_is_not_committed(self):
        case = next(c for c in simulator.scenarios() if c["id"] == "write_skew_cycle")
        self.assertEqual(simulator.decide(case, "SEMANTIC_SERIALIZABILITY")[0], "ABORT")
        self.assertEqual(simulator.decide(case, "OPTIMISTIC_VALIDATE_COMMIT")[0], "ABORT")
        raw = simulator.decide(case, "RAW_COALESCE")[1]
        self.assertEqual(raw, {"x": 1, "y": 1})
        self.assertNotIn(raw, simulator.serial_outcomes(case))

    def test_unknown_footprint_fails_closed(self):
        case = next(c for c in simulator.scenarios() if c["id"] == "unknown_overlap")
        self.assertEqual(simulator.decide(case, "UNKNOWN_AS_CONFLICT")[0], "DEFER")

    def test_raw_coalescing_retains_contributors_only_partially(self):
        case = next(c for c in simulator.scenarios() if c["id"] == "commuting_add")
        decision, final, committed = simulator.decide(case, "RAW_COALESCE")
        self.assertEqual(decision, "COALESCE")
        self.assertEqual(committed, ["p1"])
        self.assertEqual(final["x"], 1)

    def test_delayed_irreversible_conflict_serializes(self):
        case = next(c for c in simulator.scenarios() if c["id"] == "delayed_irreversible")
        decision, final, _ = simulator.decide(case, "SEMANTIC_SERIALIZABILITY")
        self.assertEqual(decision, "SERIALIZE")
        self.assertEqual(final, {"ticket": 1, "log": 1})


if __name__ == "__main__":
    unittest.main()
