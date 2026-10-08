"""Executor return evidence survives later journal edits to its retained dictionary."""
import copy
import unittest
from runtime.core_v1.compiled_gui import run
from runtime.core_v1.test_compiled_gui import Driver, interface

CAPTURED_ROWS = []

def freeze_declaration(value):
    if type(value) is dict:
        return {key: freeze_declaration(item) for key, item in value.items()}
    if type(value) is list:
        return [freeze_declaration(item) for item in value]
    if type(value) in (str, int, bool, type(None)):
        return value
    return dict(opaque_type=type(value).__name__, representation='fixture source defines this object; no copy hook invoked here')

class CopyableRelease(dict):
    def __deepcopy__(self, memo):
        return dict(verified=True, keys_down=[], buttons_down=[])

class CopyableReference:
    def __deepcopy__(self, memo):
        return 'converted-reference'

class RetainedTerminalDriver(Driver):
    def __init__(self, mode='healthy'):
        super().__init__()
        self.mode = mode
        self.cancelled = False
        self.returned = None
        self.return_time = []
        self.edits = []
        self.terminal_events = []

    def execute(self, payload):
        terminal = super().execute(payload)
        first = len(self.calls['execute']) == 1
        terminal['action_id'] = 'action-' + str(len(self.calls['execute']))
        terminal['effect_ref'] = 'effect-' + str(len(self.calls['execute']))
        if first and self.mode in ('uncertain_promoted', 'uncertain_unchanged'):
            terminal['status'] = 'delivery_uncertain'
        if first and self.mode == 'held_refusal':
            terminal.update(status='refused', input_dispatched=False,
                            release=dict(verified=False, keys_down=['CTRL'], buttons_down=[]))
        if first and self.mode == 'dispatched_refusal':
            terminal.update(status='refused', input_dispatched=True,
                            release=dict(verified=False, keys_down=[], buttons_down=[]))
        if first and self.mode == 'false_release_cleared':
            terminal['release']['verified'] = False
        if first and self.mode == 'malformed_release':
            terminal['release'] = CopyableRelease(verified=True, keys_down=[], buttons_down=[])
        if first and self.mode in ('malformed_action_id', 'malformed_effect_ref'):
            terminal[self.mode.removeprefix('malformed_')] = CopyableReference()
        self.returned = terminal
        self.return_time.append(freeze_declaration(terminal))
        return terminal

    def journal(self, payload):
        super().journal(payload)
        if payload['event'] != 'action_terminal':
            return
        self.terminal_events.append(copy.deepcopy(payload))
        if len(self.terminal_events) != 1:
            return
        before = copy.deepcopy(self.returned)
        if self.mode == 'uncertain_promoted':
            self.returned['status'] = 'completed'
        elif self.mode == 'completed_demoted':
            self.returned['status'] = 'delivery_uncertain'
        elif self.mode == 'references_rebound':
            self.returned.update(action_id='late-action', effect_ref='late-effect')
        elif self.mode == 'held_refusal':
            self.returned['release']['keys_down'].clear()
        elif self.mode == 'dispatched_refusal':
            self.returned['input_dispatched'] = False
        elif self.mode == 'false_release_cleared':
            self.returned['release']['verified'] = True
        elif self.mode == 'cancelled':
            self.cancelled = True
        self.edits.append(dict(before=before, after=copy.deepcopy(self.returned), cancelled=self.cancelled))

    def run(self):
        spec = interface()
        try:
            receipt = run(spec, dict(observe=self.observe, admit=self.admit, execute=self.execute,
                          verify_effect=self.verify, journal=self.journal, cancelled=lambda:self.cancelled),
                          clock=lambda:self.now)
        except ValueError as error:
            CAPTURED_ROWS.append(dict(mode=self.mode, graph=spec, returned_at_boundary=self.return_time,
                callbacks=freeze_declaration(self.calls), exception_type=type(error).__name__, exception=str(error)))
            raise
        CAPTURED_ROWS.append(dict(mode=self.mode, graph=spec, returned_at_boundary=self.return_time,
            later_edits=self.edits, callbacks=copy.deepcopy(self.calls), receipt=copy.deepcopy(receipt)))
        return receipt

class TerminalReturnCustodyTests(unittest.TestCase):
    def test_uncertain_return_cannot_be_promoted_to_completion(self):
        d = RetainedTerminalDriver('uncertain_promoted'); r = d.run()
        self.assertEqual((r['outcome'], r['reason'], r['completed_transitions']), ('SAFE_YIELD', 'delivery_uncertain', 0))
        self.assertEqual(len(d.calls['execute']), 1)
        self.assertEqual(d.terminal_events[0]['status'], 'delivery_uncertain')
        self.assertEqual(d.calls['verify_effect'], [])

    def test_completed_return_cannot_be_demoted_and_lose_prefix(self):
        d = RetainedTerminalDriver('completed_demoted'); r = d.run()
        self.assertEqual((r['outcome'], r['completed_transitions'], len(d.calls['execute'])), ('TASK_SUCCEEDED', 2, 2))
        self.assertEqual(d.terminal_events[0]['status'], 'completed')

    def test_action_and_effect_references_keep_return_time_identity(self):
        d = RetainedTerminalDriver('references_rebound'); r = d.run()
        self.assertEqual((r['transitions'][0]['action_id'], r['transitions'][0]['effect_ref']), ('action-1', 'effect-1'))
        self.assertEqual(d.calls['verify_effect'][0]['effect_ref'], 'effect-1')
        self.assertEqual(d.terminal_events[0]['action_id'], 'action-1')

    def test_reported_held_input_cannot_be_cleared_into_preinput_refusal(self):
        d = RetainedTerminalDriver('held_refusal'); r = d.run()
        self.assertEqual((r['outcome'], r['reason'], r['completed_transitions']), ('RUNTIME_FAILED', 'execution_failed', 0))
        self.assertEqual(len(d.calls['execute']), 1)
        self.assertIs(d.terminal_events[0]['release_verified'], False)

    def test_reported_dispatch_cannot_be_rebound_into_preinput_refusal(self):
        d = RetainedTerminalDriver('dispatched_refusal'); r = d.run()
        self.assertEqual((r['outcome'], r['reason'], r['completed_transitions']), ('RUNTIME_FAILED', 'execution_failed', 0))
        self.assertIs(d.terminal_events[0]['input_dispatched'], True)
        self.assertEqual(len(d.calls['execute']), 1)

    def test_false_release_still_fails_when_original_dictionary_is_later_cleared(self):
        d = RetainedTerminalDriver('false_release_cleared'); r = d.run()
        self.assertEqual((r['outcome'], r['reason'], r['completed_transitions']), ('RUNTIME_FAILED', 'execution_failed', 0))
        self.assertEqual(len(d.calls['execute']), 1)

    def test_actual_journal_cancellation_retains_completed_pending_prefix(self):
        d = RetainedTerminalDriver('cancelled'); r = d.run()
        self.assertEqual((r['outcome'], r['reason'], r['completed_transitions']), ('SAFE_YIELD', 'cancelled', 1))
        self.assertEqual(r['pending_effect']['effect_ref'], 'effect-1')
        self.assertEqual(len(d.calls['execute']), 1)

    def test_unchanged_uncertainty_still_stops(self):
        d = RetainedTerminalDriver('uncertain_unchanged'); r = d.run()
        self.assertEqual((r['outcome'], r['reason'], r['completed_transitions']), ('SAFE_YIELD', 'delivery_uncertain', 0))
        self.assertEqual(len(d.calls['execute']), 1)

    def test_healthy_two_step_completion_is_preserved(self):
        d = RetainedTerminalDriver(); r = d.run()
        self.assertEqual((r['outcome'], r['completed_transitions'], len(d.calls['execute'])), ('TASK_SUCCEEDED', 2, 2))
        self.assertIsNone(r['pending_effect'])

    def test_original_release_subclass_cannot_be_coerced_by_copy_hook(self):
        d = RetainedTerminalDriver('malformed_release')
        with self.assertRaises(ValueError):
            d.run()
        self.assertEqual(len(d.calls['execute']), 1)
        self.assertEqual(d.terminal_events, [])

    def test_original_nonstring_references_cannot_be_coerced_by_copy_hook(self):
        for field in ('action_id', 'effect_ref'):
            with self.subTest(field=field):
                d = RetainedTerminalDriver('malformed_' + field)
                with self.assertRaises(ValueError):
                    d.run()
                self.assertEqual(len(d.calls['execute']), 1)
                self.assertEqual(d.calls['verify_effect'], [])

if __name__ == '__main__':
    unittest.main()
