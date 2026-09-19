"""Run the real harness loop with inert application/input dependencies."""
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch


class NativeFinishAfterTests(unittest.TestCase):
    def exercise(self, decisions, *, task_success=True, action_status='completed',
                 close_failure=False, expected_error=None, max_stages=4, inspect_goal=None,
                 focus_within=True, review_status='reviewed'):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            out = root / 'out'
            output = root / 'shape.svg'; output.write_text('inert saved fixture')
            events = []
            remaining = iter(decisions)

            class Session:
                name = ':inert'
                procs = []

                def windows(self):
                    return '0x00000001 host shape.svg - Inkscape'

                def close(self):
                    events.append('session.close')

            class Bridge:
                def __init__(self, *args):
                    self.backend = SimpleNamespace(targets={'app': SimpleNamespace(id=1)})

                def observe(self):
                    return {'sequence': 1, 'native': {'artifact': {'path': 'inert.png'}}}

                def mint(self, *args, **kwargs):
                    events.append('mint')
                    return [12, 7]

                def click(self, *args, **kwargs):
                    events.append('input')
                    return {'status': action_status}

                keyboard = click

                def feedback(self, *args, **kwargs):
                    return {'status': 'matched'}

                def _focus_within_target(self):
                    return focus_within

                def focused_client_window(self):
                    return 2

                def review_window(self, window):
                    assert window == (1 if focus_within else 2)
                    return {'status': review_status, 'observation': {
                        'sequence': 2, 'native': {'artifact': {'path': 'inert-final.png'}}}}

                def close(self):
                    events.append('bridge.close')
                    # Terminal reply must not be published before cleanup.
                    if decisions[-1].get('finish_after') is True:
                        assert not (out / f'reply-{len(decisions)}.json').exists()
                    if close_failure:
                        raise OSError('injected connection cleanup failure')

            def evaluate(*args):
                events.append('evaluate')
                return {'success': task_success, 'actual': 'inert'}

            suite = SimpleNamespace(prepare=lambda *a: ({'dx': 36}, output, None), evaluate=evaluate)
            prerequisite = SimpleNamespace(PrivateSession=Session, suite=suite)
            spec = importlib.util.spec_from_file_location('native_finish_harness_under_test',
                Path(__file__).with_name('run_native_calc_self_use_v1.py'))
            subject = importlib.util.module_from_spec(spec)
            # Replace only this dependency; do not roll back unrelated modules
            # imported during harness loading (notably NumPy extension state).
            key = 'run_native_six_task_self_use_v1'
            previous = sys.modules.get(key)
            sys.modules[key] = prerequisite
            try:
                spec.loader.exec_module(subject)
            finally:
                if previous is None:
                    sys.modules.pop(key)
                else:
                    sys.modules[key] = previous

            def supply_request(_seconds):
                stage = len(list(out.glob('request-*.json'))) + 1
                if inspect_goal is not None:
                    inspect_goal(json.loads((out / 'goal.json').read_text()))
                decision = next(remaining)  # Unexpected extra wait is a test failure.
                source = json.loads((out / f'source-{stage}.json').read_text())
                subject.publish(out / f'request-{stage}.json', subject.encoded(
                    dict(source_sequence=source['sequence'], **decision)))

            with patch.object(subject, 'NativeHandleBridge', Bridge), \
                 patch.object(subject.time, 'sleep', supply_request), \
                 patch.object(sys, 'argv', ['harness', '--app', 'inkscape', '--out', str(out),
                                            '--max-stages', str(max_stages)]), \
                 patch('builtins.print'):
                if expected_error:
                    with self.assertRaises(expected_error): subject.main()
                else:
                    subject.main()
            replies = [json.loads(p.read_text()) for p in sorted(out.glob('reply-*.json'))]
            sources = [p.name for p in out.glob('source-*.json')]
            self.assertEqual(events[-1], 'session.close')
            self.assertEqual(len(replies), len(decisions))
            return replies, sources, events

    def action(self, **extra):
        return dict(point=[600, 378], expected_title='shape.svg - Inkscape', tail=[], **extra)

    def test_finish_after_one_response_after_cleanup(self):
        replies, sources, events = self.exercise([self.action(finish_after=True)])
        self.assertEqual(sources, ['source-1.json'])
        self.assertEqual(replies[0]['status'], 'finished')
        self.assertEqual(replies[0]['observation']['sequence'], 2)
        self.assertEqual(replies[0]['cleanup']['status'], 'completed')
        self.assertEqual(events, ['mint', 'input', 'evaluate', 'bridge.close', 'session.close'])

    def test_directional_task_is_public_before_first_decision(self):
        seen = []
        def inspect(goal):
            task = goal['task']
            self.assertEqual(task['kind'], 'move_right_preserve_geometry')
            self.assertEqual(task['coordinate_frame'], 'svg_user_units')
            self.assertEqual(task['dx_meaning'], 'nominal_drag_screen_px_not_exact_keyboard_displacement')
            self.assertEqual((task['x_greater_than'], task['y'], task['width'], task['height']),
                             (50.5, 50, 40, 30))
            self.assertEqual(task['geometry_tolerance_exclusive'], 0.1)
            self.assertIsNone(task['transform'])
            self.assertEqual(task['save_format'], 'svg')
            seen.append(goal)
        self.exercise([self.action(finish_after=True)], inspect_goal=inspect)
        self.assertEqual(len(seen), 1)

    def test_finish_after_on_last_permitted_stage(self):
        replies,sources,events=self.exercise(
            [self.action(),self.action(finish_after=True)],max_stages=2)
        self.assertEqual([r['status'] for r in replies],['boundary','finished'])
        self.assertEqual(set(sources),{'source-1.json','source-2.json'})
        self.assertEqual(events.count('input'),2)
        self.assertEqual(events.count('evaluate'),1)
        self.assertEqual(replies[-1]['cleanup']['status'],'completed')

    def test_default_and_false_still_wait_for_explicit_finish(self):
        for extra in ({}, {'finish_after': False}):
            with self.subTest(extra=extra):
                replies, sources, _ = self.exercise([self.action(**extra), {'finish': True}])
                self.assertEqual([r['status'] for r in replies], ['boundary', 'finished'])
                self.assertEqual(len(sources), 2)

    def test_failed_task_is_retained_in_finished_session(self):
        replies, _, _ = self.exercise([self.action(finish_after=True)], task_success=False)
        self.assertEqual(replies[0]['status'], 'finished')
        self.assertIs(replies[0]['evaluation']['success'], False)

    def test_explicit_observation_neither_mints_nor_dispatches_input(self):
        replies, sources, events = self.exercise([{'interaction': 'observe'}, {'finish': True}])
        self.assertEqual([r['status'] for r in replies], ['boundary', 'finished'])
        self.assertEqual(set(sources), {'source-1.json', 'source-2.json'})
        self.assertEqual(replies[0]['observation_only']['captures'], 1)
        self.assertFalse(replies[0]['observation_only']['input_dispatched'])
        self.assertNotIn('action', replies[0])
        self.assertNotIn('input', events)
        self.assertNotIn('mint', events)

    def test_observation_rejects_hidden_input_fields(self):
        replies, _, events = self.exercise([{'interaction': 'observe', 'tail': []}],
                                            expected_error=ValueError)
        self.assertEqual(replies[0]['status'], 'needs_review')
        self.assertNotIn('mint', events)

    def test_observation_reviews_changed_focus_without_input(self):
        replies, _, events = self.exercise([{'interaction': 'observe'}, {'finish': True}],
                                            focus_within=False)
        self.assertEqual(replies[0]['observation']['sequence'], 2)
        self.assertEqual(replies[0]['observation_only']['window_review']['status'], 'reviewed')
        self.assertNotIn('mint', events)
        self.assertNotIn('input', events)

    def test_observation_failed_window_review_never_publishes_next_source(self):
        replies, sources, events = self.exercise([{'interaction': 'observe'}],
            focus_within=False, review_status='needs_review', expected_error=RuntimeError)
        self.assertEqual(sources, ['source-1.json'])
        self.assertEqual(replies[0]['status'], 'needs_review')
        self.assertNotIn('mint', events)
        self.assertNotIn('input', events)

    def test_invalid_or_conflicting_flags_precede_mint(self):
        for decision in ({'finish_after': 'true'}, {'finish_after': 1},
                         {'finish_after': True, 'finish': True}):
            with self.subTest(decision=decision):
                replies, _, events = self.exercise([decision], expected_error=ValueError)
                self.assertEqual(replies[0]['status'], 'needs_review')
                self.assertEqual(events, ['bridge.close', 'session.close'])

    def test_failed_input_is_not_evaluated_or_replayed(self):
        replies, _, events = self.exercise([self.action(finish_after=True)],
            action_status='refused', expected_error=RuntimeError)
        self.assertEqual(replies[0]['status'], 'needs_review')
        self.assertNotIn('evaluation', replies[0])
        self.assertNotIn('evaluate', events)
        self.assertEqual(events.count('input'), 1)

    def test_cleanup_failure_preserves_action_image_and_evaluation(self):
        replies, _, _ = self.exercise([self.action(finish_after=True)],
            close_failure=True, expected_error=RuntimeError)
        self.assertEqual(replies[0]['status'], 'needs_review')
        self.assertEqual(replies[0]['observation']['sequence'], 2)
        self.assertTrue(replies[0]['evaluation']['success'])
        self.assertEqual(replies[0]['cleanup']['status'], 'needs_review')


if __name__ == '__main__':
    unittest.main()
