"""Independent success scoring for the synthetic Xvfb cancellation task."""

import unittest


def score_synthetic_application_task(*, initial_effect, final_effect,
                                     release_readback, horizon_readback):
    """Value/key-state evidence only; does not establish effect multiplicity."""
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


def _valid_effect_count(value):
    return (type(value) is list and len(value) == 1
            and type(value[0]) is int and 0 <= value[0] < 2**32)


def score_synthetic_effect_counts(*, before_count, after_count, horizon_count):
    """Require one non-idempotent effect from a fresh zero-count fixture."""
    if not all(_valid_effect_count(value) for value in
               (before_count, after_count, horizon_count)):
        return {'status':'unknown', 'task_success':None,
                'reason':'incomplete_or_malformed_effect_count'}
    checks = {'effect_count_before_exact':before_count == [0],
              'effect_count_after_exact':after_count == [1],
              'effect_count_horizon_exact':horizon_count == [1]}
    success = all(checks.values())
    return {'status':'pass' if success else 'fail',
            'task_success':success, 'checks':checks}


def score_counted_synthetic_application_task(*, initial_effect, final_effect,
        initial_effect_count, final_effect_count, release_readback, horizon_readback):
    value = score_synthetic_application_task(initial_effect=initial_effect,
        final_effect=final_effect, release_readback=release_readback,
        horizon_readback=horizon_readback)
    if (value['status'] == 'unknown' or not _valid_effect_count(initial_effect_count)
            or not _valid_effect_count(final_effect_count)):
        return {'status':'unknown', 'task_success':None,
                'reason':'incomplete_or_malformed_evidence'}
    checks = dict(value['checks'], initial_effect_count_exact=initial_effect_count == [1],
                  final_effect_count_exact=final_effect_count == [1])
    success = all(checks.values())
    return {'status':'pass' if success else 'fail',
            'task_success':success, 'checks':checks}


def score_recovered_synthetic_application_task(*, initial_effect, final_effect,
                                               release_readback, horizon_readback,
                                               expected_initial, expected_final):
    """Legacy value/key-state task; no effect-count or exactly-once evidence."""
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


class CountedSyntheticTaskOracleTests(unittest.TestCase):
    def score(self, initial=[1], final=[1]):
        from runtime.cli_v1.test_synthetic_task_oracle import score_counted_synthetic_application_task
        return score_counted_synthetic_application_task(
            initial_effect=[1], final_effect=[1],
            initial_effect_count=initial, final_effect_count=final,
            release_readback={'a':False, 'b':False},
            horizon_readback={'a':False, 'b':False})

    def test_repeated_handlers_cannot_pass_with_same_final_value(self):
        result = self.score(final=[3])
        self.assertEqual(result['status'], 'fail')
        self.assertFalse(result['task_success'])
        self.assertFalse(result['checks']['final_effect_count_exact'])

    def test_one_effect_is_required_both_before_cancel_and_at_horizon(self):
        self.assertTrue(self.score()['task_success'])
        for initial, final in [([0], [1]), ([2], [2]), ([1], [0])]:
            with self.subTest(initial=initial, final=final):
                self.assertFalse(self.score(initial, final)['task_success'])

    def test_missing_or_malformed_count_stays_unknown(self):
        for value in (None, [], [True], [-1], [1, 1], [2**32], 1):
            for initial, final in ((value, [1]), ([1], value)):
                with self.subTest(initial=initial, final=final):
                    result = self.score(initial, final)
                    self.assertEqual(result['status'], 'unknown')
                    self.assertIsNone(result['task_success'])

    def test_count_does_not_override_wrong_effect_or_held_input(self):
        from runtime.cli_v1.test_synthetic_task_oracle import score_counted_synthetic_application_task
        for effect, key_down in (([2], False), ([1], True)):
            result = score_counted_synthetic_application_task(
                initial_effect=[1], final_effect=effect,
                initial_effect_count=[1], final_effect_count=[1],
                release_readback={'a':key_down, 'b':False},
                horizon_readback={'a':False, 'b':False})
            self.assertFalse(result['task_success'])

    def test_fresh_count_transition_rejects_late_duplicate(self):
        from runtime.cli_v1.test_synthetic_task_oracle import score_synthetic_effect_counts
        for before, after, horizon, expected in (([0], [1], [1], True),
                ([0], [1], [2], False), ([1], [1], [1], False)):
            result = score_synthetic_effect_counts(
                before_count=before, after_count=after, horizon_count=horizon)
            self.assertIs(result['task_success'], expected)

    def test_fresh_count_transition_keeps_absent_evidence_unknown(self):
        from runtime.cli_v1.test_synthetic_task_oracle import score_synthetic_effect_counts
        for values in ((None, [1], [1]), ([0], [True], [1]), ([0], [1], [])):
            result = score_synthetic_effect_counts(before_count=values[0],
                after_count=values[1], horizon_count=values[2])
            self.assertEqual(result['status'], 'unknown')
            self.assertIsNone(result['task_success'])
