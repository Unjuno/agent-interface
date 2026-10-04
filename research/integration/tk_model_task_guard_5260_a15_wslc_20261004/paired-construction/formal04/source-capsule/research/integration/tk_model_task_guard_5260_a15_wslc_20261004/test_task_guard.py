"""Construct the joined admission predicate before any new GUI/model allocation."""
import importlib.util
import unittest
from copy import deepcopy

BINDING = {'pid': 42, 'token': 'new-construction-task',
           'root_id': 101, 'target_id': 102, 'freeze_sha256': 'f' * 64}


def snapshot(target='bqt', decoy='', focus='target'):
    return {'binding': deepcopy(BINDING), 'nonce': 'post-model-1',
            'sequence': 7, 'started_ns': 210, 'completed_ns': 220,
            'target': target, 'decoy': decoy, 'focus': focus}


def answer(decision='NO_REPAIR', target='bqt', decoy='', prefix=''):
    return {'decision': decision, 'observed_target': target,
            'observed_decoy': decoy, 'prefix': prefix}


class TaskGuardTests(unittest.TestCase):
    def module(self):
        self.assertIsNotNone(importlib.util.find_spec('task_guard'),
                             'joined current-task guard missing')
        import task_guard
        return task_guard

    def decide(self, review, current=None, **changes):
        options = {'wanted': 'bqt', 'expected_binding': BINDING,
                   'request_nonce': 'post-model-1', 'image_sequence': 6,
                   'response_seen_ns': 200, 'now_ns': 230, 'max_age_ns': 50}
        options.update(changes)
        return self.module().decide_review(review, snapshot() if current is None else current, **options)

    def test_exact_review_can_only_propose_a_separately_guarded_save(self):
        result = self.decide(answer())
        self.assertEqual(result['status'], 'PLAN_SAVE')
        self.assertIs(result['grants_input_authority'], False)
        self.assertIs(result['task_complete'], False)

    def test_wrong_no_repair_cannot_finish_or_save_missing_prefix(self):
        result = self.decide(answer(), snapshot('qt'))
        self.assertEqual(result['status'], 'YIELD')
        self.assertEqual(result['reason'], 'MODEL_STATE_MISMATCH')
        self.assertIs(result['grants_input_authority'], False)
        self.assertIs(result['task_complete'], False)

    def test_missing_prefix_plan_preserves_only_the_model_suggestion(self):
        result = self.decide(answer('INSERT_PREFIX', 'qt', prefix='b'), snapshot('qt'))
        self.assertEqual(result['status'], 'PLAN_PREFIX')
        self.assertEqual(result['prefix'], 'b')
        self.assertEqual(result['expected_target'], 'bqt')
        self.assertIs(result['grants_input_authority'], False)
        for prefix in ('x', 'bb'):
            with self.subTest(prefix=prefix):
                self.assertEqual(self.decide(answer('INSERT_PREFIX', 'qt', prefix=prefix),
                                             snapshot('qt'))['status'], 'YIELD')

    def test_decoy_ambiguous_and_explicit_refusal_cannot_be_repaired_locally(self):
        cases = [
            (answer('REFUSE', '', 'bqt'), snapshot('', 'bqt')),
            (answer('INSERT_PREFIX', 'zz', prefix='b'), snapshot('zz')),
            (answer('REFUSE'), snapshot()),
            (answer(), snapshot('bqt', 'other'))]
        for review, current in cases:
            with self.subTest(review=review, current=current):
                self.assertEqual(self.decide(review, current)['status'], 'YIELD')

    def test_current_focus_drift_invalidates_an_otherwise_correct_answer(self):
        result = self.decide(answer(), snapshot(focus='decoy'))
        self.assertEqual(result['status'], 'YIELD')
        self.assertEqual(result['reason'], 'FOCUS_NOT_TARGET')

    def test_old_future_replayed_or_unbound_snapshots_do_not_admit(self):
        controls = []
        for name, value in [('sequence', 6), ('sequence', True),
                            ('nonce', 'old-request'), ('started_ns', 199),
                            ('completed_ns', 240), ('completed_ns', 209)]:
            current = snapshot(); current[name] = value; controls.append(current)
        current = snapshot(); current['binding']['pid'] = 43; controls.append(current)
        current = snapshot(); current['binding']['pid'] = True; controls.append(current)
        current = snapshot(); del current['target']; controls.append(current)
        for current in controls:
            with self.subTest(current=current):
                self.assertEqual(self.decide(answer(), current)['status'], 'YIELD')
        self.assertEqual(self.decide(answer(), now_ns=271)['status'], 'YIELD')

    def test_repair_must_reconcile_a_later_current_effect_before_save_proposal(self):
        module = self.module()
        self.assertTrue(hasattr(module, 'verify_repair_effect'), 'repair effect guard missing')
        proposal = self.decide(answer('INSERT_PREFIX', 'qt', prefix='b'), snapshot('qt'))
        after = snapshot(); after.update(nonce='post-input-1', sequence=8,
                                         started_ns=310, completed_ns=320)
        options = {'request_nonce': 'post-input-1', 'action_finished_ns': 300,
                   'now_ns': 330, 'max_age_ns': 50}
        result = module.verify_repair_effect(proposal, after, **options)
        self.assertEqual(result['status'], 'PLAN_SAVE')
        self.assertIs(result['grants_input_authority'], False)
        self.assertIs(result['task_complete'], False)
        for field, value in [('target', 'qt'), ('decoy', 'b'), ('sequence', 7),
                             ('started_ns', 299), ('focus', 'decoy')]:
            changed = deepcopy(after); changed[field] = value
            with self.subTest(field=field):
                self.assertEqual(module.verify_repair_effect(proposal, changed, **options)['status'], 'YIELD')

    def test_repair_completion_cannot_precede_its_reviewed_snapshot(self):
        module = self.module()
        proposal = self.decide(answer('INSERT_PREFIX', 'qt', prefix='b'), snapshot('qt'))
        after = snapshot(); after.update(nonce='post-input-1', sequence=8,
                                         started_ns=310, completed_ns=320)
        result = module.verify_repair_effect(proposal, after,
            request_nonce='post-input-1', action_finished_ns=219, now_ns=330, max_age_ns=50)
        self.assertEqual(result['status'], 'YIELD')
        self.assertEqual(result['reason'], 'REPAIR_CLOCK')


if __name__ == '__main__':
    unittest.main()
