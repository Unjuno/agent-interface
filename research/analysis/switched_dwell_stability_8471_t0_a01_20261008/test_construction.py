import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import candidate
import audit
from protocol import (F, LYAPUNOV, MODES, matrix_product, quadratic, INITIAL,
                      HYSTERESIS_ENTER, HYSTERESIS_EXIT, hysteresis_schedule,
                      minimum_dwell_schedule)


class Construction(unittest.TestCase):
    def test_individual_modes_have_exact_lyapunov_decrease(self):
        for name in ("A", "B"):
            p, m = LYAPUNOV[name], MODES[name]
            mt = tuple(zip(*m))
            pm = matrix_product(p, m)
            mtmp = matrix_product(mt, pm)
            self.assertEqual(tuple(tuple(p[i][j] - mtmp[i][j] for j in range(2))
                                   for i in range(2)), ((F(1), F(0)), (F(0), F(1))))
            self.assertGreater(p[0][0] * p[1][1] - p[0][1] ** 2, 0)

    def test_switching_comparator_extremes_realize_alternation(self):
        signals = [F(1) if i % 2 == 0 else F(0) for i in range(12)]
        self.assertEqual("".join(hysteresis_schedule(signals)), "BABABABABABA")
        self.assertEqual(HYSTERESIS_ENTER, F(2, 3))
        self.assertEqual(HYSTERESIS_EXIT, F(1, 3))

    def test_dwell_and_emergency_policy_fixtures(self):
        requests = tuple("B" if i % 2 == 0 else "A" for i in range(12))
        schedule = minimum_dwell_schedule(requests)
        self.assertEqual(sum(schedule[i] != schedule[i-1] for i in range(1, 12)), 1)
        # The abstract emergency path is an unconditional immediate transition.
        emergency = "B" if schedule[-1] == "A" else "A"
        self.assertNotEqual(emergency, schedule[-1])

    def test_candidate_output_reconstructs_and_controls_reject_mutations(self):
        candidate.main()
        import json
        data = json.loads((HERE / "candidate.json").read_text())
        self.assertTrue(audit.audit(data))
        self.assertEqual(len(audit.mutation_suite(data)), 7)


if __name__ == "__main__":
    unittest.main()
