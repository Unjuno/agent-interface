import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).parent

class PortfolioProbeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = subprocess.run([sys.executable, str(ROOT / 'candidate.py')], cwd=ROOT, text=True, capture_output=True, check=True)
        cls.data = json.loads(cls.result.stdout)

    def test_session_prep_amortizes_both_controls_on_repeated_tasks(self):
        self.assertEqual(self.data['formal_invocations'], 0)
        self.assertEqual(self.data['construction_invocations'], 1)
        arms = self.data['families']['repeated_same_target']['arms']
        self.assertEqual(arms['none']['total_cost'], 15)
        self.assertEqual(arms['per_task']['total_cost'], 18)
        self.assertEqual(arms['session']['total_cost'], 12)
        self.assertTrue(all(arms[name]['all_effects_exact'] for name in ('none', 'per_task', 'session')))

    def test_session_prep_refuses_heterogeneous_warning_obscuring_state(self):
        row = self.data['families']['heterogeneous_warning']['arms']['session']
        self.assertEqual(row['disposition'], 'DEFERRED_SAFETY')
        self.assertFalse(row['critical_warning_visible'])
        self.assertNotIn('total_cost', row)
        self.assertEqual(row['incurred_cost'], 8)
        self.assertEqual(row['consequential_actions_after_warning_hidden'], 0)

    def test_partial_restore_is_unknown_not_complete(self):
        row = self.data['controls']['partial_restore']
        self.assertEqual(row['disposition'], 'UNKNOWN_RESTORE')
        self.assertFalse(row['restoration_complete'])

    def test_competing_generation_change_blocks_stale_preparation(self):
        row = self.data['controls']['competing_edit']
        self.assertEqual(row['disposition'], 'DEFERRED_STALE_GENERATION')
        self.assertEqual(row['consequential_actions_after_generation_change'], 0)

    def test_callback_side_effect_is_not_misreported_as_restored(self):
        row = self.data['controls']['callback_side_effect']
        self.assertEqual(row['disposition'], 'REJECTED_COLLATERAL')
        self.assertTrue(row['user_state_changed'])
        self.assertFalse(row['restoration_complete'])

if __name__ == '__main__':
    unittest.main()
