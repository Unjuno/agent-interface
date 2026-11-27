import unittest
from unittest import mock

from research.doom import analyze_map01_direct_retained_input_v2 as analyzer
from research.live_control import test_input_transition_owner_v3 as owner_test


class ReceiptToAnalyzerIntegrationTests(unittest.TestCase):
    def test_owner_release_receipt_produces_bounded_per_key_measurement(self):
        owner = owner_test.mod.InputOwner(
            ':fake', _owner_cls=owner_test.ExplicitUpBatchInner)
        lease = owner_test.Lease(deadline=1000)

        admission = owner.call('down', lease, 'w')
        admission['owner_id'] = owner.owner_id
        with mock.patch.object(owner_test.mod.time, 'perf_counter_ns',
                               side_effect=[100, 140]):
            release = owner.call('up_batch', lease, ['w'])[0]

        result = analyzer.analyze([admission, release])

        self.assertTrue(result['measurement_ready'])
        self.assertEqual(result['hold_count'], 1)
        self.assertEqual(result['unmatched_admission_count'], 0)
        self.assertEqual(result['invalid_release_count'], 0)
        hold = result['holds'][0]
        self.assertEqual(hold['key'], 'w')
        self.assertEqual(hold['retained_lower_ms'], 10 / 1e6)
        self.assertEqual(hold['retained_upper_ms'], 60 / 1e6)
        self.assertEqual(hold['censor_width_ms'], 50 / 1e6)
        self.assertIs(release['grants_input_authority'], False)


if __name__ == '__main__':
    unittest.main()
