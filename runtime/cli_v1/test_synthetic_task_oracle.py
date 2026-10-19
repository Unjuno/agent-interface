"""Independent success scoring for the synthetic Xvfb cancellation task."""

import unittest


def score_synthetic_application_task(*, initial_effect, final_effect,
                                     release_readback, horizon_readback):
    effects = (initial_effect, final_effect)
    states = (release_readback, horizon_readback)
    if (any(type(value) is not list
            or any(type(item) is not int for item in value)
            for value in effects)
            or any(type(state) is not dict
                   or set(state) != {'a', 'b'}
                   or any(type(value) is not bool for value in state.values())
                   for state in states)):
        return {'status':'unknown', 'task_success':None,
                'reason':'incomplete_or_malformed_evidence'}

    checks = {
        'initial_effect_exact':initial_effect == [1],
        'final_effect_exact':final_effect == [1],
        'release_readback_all_up':release_readback == {'a':False, 'b':False},
        'horizon_readback_all_up':horizon_readback == {'a':False, 'b':False},
    }
    task_success = all(checks.values())
    return {'status':'pass' if task_success else 'fail',
            'task_success':task_success, 'checks':checks}


class SyntheticTaskOracleTests(unittest.TestCase):
    def test_scores_exact_effect_and_persistent_release_as_success(self):
        result = score_synthetic_application_task(
            initial_effect=[1], final_effect=[1],
            release_readback={'a':False, 'b':False},
            horizon_readback={'a':False, 'b':False})

        self.assertEqual(result, {
            'status':'pass', 'task_success':True,
            'checks':{
                'initial_effect_exact':True,
                'final_effect_exact':True,
                'release_readback_all_up':True,
                'horizon_readback_all_up':True,
            },
        })

    def test_scores_late_wrong_effect_as_failure(self):
        result = score_synthetic_application_task(
            initial_effect=[1], final_effect=[2],
            release_readback={'a':False, 'b':False},
            horizon_readback={'a':False, 'b':False})

        self.assertEqual(result['status'], 'fail')
        self.assertFalse(result['task_success'])
        self.assertFalse(result['checks']['final_effect_exact'])

    def test_scores_key_still_down_after_release_as_failure(self):
        result = score_synthetic_application_task(
            initial_effect=[1], final_effect=[1],
            release_readback={'a':False, 'b':True},
            horizon_readback={'a':False, 'b':True})

        self.assertEqual(result['status'], 'fail')
        self.assertFalse(result['task_success'])
        self.assertFalse(result['checks']['release_readback_all_up'])

    def test_keeps_malformed_or_incomplete_evidence_unknown(self):
        result = score_synthetic_application_task(
            initial_effect=[1], final_effect=[1],
            release_readback={'a':0, 'b':False},
            horizon_readback={'a':False, 'b':False})

        self.assertEqual(result, {
            'status':'unknown', 'task_success':None,
            'reason':'incomplete_or_malformed_evidence',
        })
