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


def score_recovered_synthetic_application_task(*, initial_effect, final_effect,
                                               release_readback, horizon_readback,
                                               expected_initial, expected_final):
    effects = (initial_effect, final_effect, expected_initial, expected_final)
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
        'initial_effect_exact':initial_effect == expected_initial,
        'final_effect_exact':final_effect == expected_final,
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


class RecoveredSyntheticTaskOracleTests(unittest.TestCase):
    def test_scores_new_effect_after_recovery_with_independent_keyup_readbacks(self):
        from runtime.cli_v1.test_synthetic_task_oracle import (
            score_recovered_synthetic_application_task,
        )

        result = score_recovered_synthetic_application_task(
            initial_effect=[1], final_effect=[2],
            release_readback={'a':False, 'b':False},
            horizon_readback={'a':False, 'b':False},
            expected_initial=[1], expected_final=[2])

        self.assertEqual(result, {
            'status':'pass', 'task_success':True,
            'checks':{
                'initial_effect_exact':True,
                'final_effect_exact':True,
                'release_readback_all_up':True,
                'horizon_readback_all_up':True,
            },
        })

    def test_fails_when_recovery_has_no_new_effect_or_leaves_a_key_down(self):
        from runtime.cli_v1.test_synthetic_task_oracle import (
            score_recovered_synthetic_application_task,
        )

        result = score_recovered_synthetic_application_task(
            initial_effect=[1], final_effect=[1],
            release_readback={'a':False, 'b':False},
            horizon_readback={'a':False, 'b':True},
            expected_initial=[1], expected_final=[2])

        self.assertEqual(result['status'], 'fail')
        self.assertFalse(result['task_success'])
        self.assertFalse(result['checks']['final_effect_exact'])
        self.assertFalse(result['checks']['horizon_readback_all_up'])

    def test_malformed_recovery_evidence_remains_unknown(self):
        from runtime.cli_v1.test_synthetic_task_oracle import (
            score_recovered_synthetic_application_task,
        )

        result = score_recovered_synthetic_application_task(
            initial_effect=[1], final_effect=[2],
            release_readback={'a':False, 'b':0},
            horizon_readback={'a':False, 'b':False},
            expected_initial=[1], expected_final=[2])

        self.assertEqual(result, {
            'status':'unknown', 'task_success':None,
            'reason':'incomplete_or_malformed_evidence',
        })
