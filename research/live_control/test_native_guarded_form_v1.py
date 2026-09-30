import copy
import unittest
from unittest.mock import Mock
from native_guarded_form_v1 import fill_and_submit


def completed():
    return {'status': 'completed', 'recovery_required': False,
            'execution': {'releases': [{'verified': True, 'keys_down': [], 'buttons_down': []}]}}


class GuardedFormTests(unittest.TestCase):
    handles = {'field': ('field', [12, 19]), 'submit': ('save', [12, 7])}

    def test_persisted_first_result_precedes_second_target_dispatch(self):
        events = []
        bridge = Mock()
        bridge.click.side_effect = lambda alias, offset, **kw: events.append(('click', alias)) or completed()
        row = fill_and_submit(bridge, self.handles, 'token', wait_ms=100,
            on_step=lambda name, result: events.append(('persist', name)))
        self.assertEqual(events, [('click','field'),('persist','entered'),('click','save'),('persist','saved')])
        self.assertEqual(row['completed_actions'], 2)
        self.assertIsNone(row['task_success'])
        self.assertFalse(row['replay_allowed'])

    def test_failed_or_unverified_entry_never_clicks_submit(self):
        variants = [dict(status='refused', input_dispatched=False), dict(status='failed'),
                    completed(), completed(), completed(), completed()]
        variants[2]['execution']['releases'][0]['verified'] = False
        variants[3]['execution']['releases'][0]['keys_down'] = ['CTRL']
        variants[4]['execution']['releases'] = []
        variants[5]['recovery_required'] = True
        for first in variants:
            with self.subTest(first=first):
                bridge=Mock();bridge.click.return_value=first; retained=[]
                row=fill_and_submit(bridge,self.handles,'token',wait_ms=100,
                    on_step=lambda name,result:retained.append((name,copy.deepcopy(result))))
                self.assertEqual(bridge.click.call_count,1)
                self.assertEqual(row['status'],'safe_yield')
                self.assertEqual(row['stopped_at'],'entered')
                self.assertEqual(retained,[('entered',first)])

    def test_second_refusal_retains_completed_first_effect_without_retry(self):
        first=completed();second={'status':'refused','input_dispatched':False}
        bridge=Mock();bridge.click.side_effect=[first,second]
        row=fill_and_submit(bridge,self.handles,'token',wait_ms=0,on_step=lambda *_:None)
        self.assertEqual(row['completed_actions'],1)
        self.assertEqual(row['results'],{'entered':first,'saved':second})
        self.assertEqual(bridge.click.call_count,2)

    def test_persistence_or_uncertain_dispatch_error_never_retries(self):
        for uncertain in (False,True):
            bridge=Mock();bridge.click.side_effect=RuntimeError('uncertain') if uncertain else None
            bridge.click.return_value=completed()
            def retain(*_):raise OSError('disk')
            with self.assertRaises((RuntimeError,OSError)):
                fill_and_submit(bridge,self.handles,'token',wait_ms=100,on_step=retain)
            self.assertEqual(bridge.click.call_count,1)

    def test_all_references_and_options_checked_before_input(self):
        for handles,wait in [({'field':('f',[1,2])},100),
                             ({'field':('f',[1,2]),'submit':('s',[True,2])},100),
                             (self.handles,True),(self.handles,1001)]:
            bridge=Mock()
            with self.assertRaises(ValueError):
                fill_and_submit(bridge,handles,'token',wait_ms=wait,on_step=lambda *_:None)
            bridge.click.assert_not_called()
