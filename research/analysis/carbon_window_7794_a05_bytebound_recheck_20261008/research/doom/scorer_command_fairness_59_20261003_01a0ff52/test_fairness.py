import os
import unittest
from assay import COMMAND, run_case

class FinishService(unittest.TestCase):
    def test_already_ready_finish_survives_every_sample_at_period_cost(self):
        for component in ('loop', 'stdin'):
            with self.subTest(component=component):
                row = run_case(os.environ.get('FAIRNESS_VARIANT', 'retained'), component, 'period_sample')
                self.assertEqual(row['commands'], [COMMAND], row['outcome'])
                self.assertEqual(row['outcome'], 'finish_served')

if __name__ == '__main__':
    unittest.main()
