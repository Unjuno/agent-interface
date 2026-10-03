"""Ordinary engineering regression after preserved A01 oracle failure."""
import json
import os
from pathlib import Path
import unittest
from assay import COMMAND, run_case

class FirstSampleDelivery(unittest.TestCase):
    def test_ready_finish_is_served_after_one_completed_sample(self):
        rows = []
        variant = os.environ.get('FAIRNESS_VARIANT', 'fair')
        for component in ('loop', 'stdin'):
            for scenario in ('zero', 'half_sample', 'period_sample', 'double_sample',
                             'ten_sample', 'half_sink', 'period_sink', 'double_sink', 'ten_sink'):
                row = run_case(variant, component, scenario)
                rows.append(row)
                with self.subTest(component=component, scenario=scenario):
                    self.assertEqual(row['commands'], [COMMAND])
                    self.assertEqual(row['samples'], 1)
                    self.assertEqual(row['final_clock_ns'], row['sample_cost_ns'] + row['sink_cost_ns'])
                    self.assertTrue(all(e['thread_id'] == row['owner_thread'] for e in row['events']))
        if 'FAIRNESS_REGRESSION_RAW' in os.environ:
            with Path(os.environ['FAIRNESS_REGRESSION_RAW']).open('x') as f:
                for row in rows:
                    f.write(json.dumps(row, sort_keys=True) + '\n')

if __name__ == '__main__':
    unittest.main()
