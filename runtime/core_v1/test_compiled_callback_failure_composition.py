"""Post-dispatch callback failure preserves current core evidence; inert only."""
import copy
import unittest
from runtime.core_v1 import test_compiled_gui as fixtures
from runtime.core_v1 import compiled_gui

ROWS=[]


def cell(journal_at=None,verify_failure=False,mutate=False):
    driver=fixtures.Driver();events=[]
    def journal(event):
        events.append(copy.deepcopy(event));driver.record('journal',copy.deepcopy(event))
        fault=event['event']==journal_at
        if mutate:event.clear()
        if fault:raise OSError('owned journal failure')
    def verify(payload):
        driver.record('verify_effect',payload)
        if verify_failure:raise RuntimeError('owned verifier failure')
        return {'status':'succeeded','evidence_ref':payload['observation']['evidence_ref']}
    try:
        result=compiled_gui.run(fixtures.interface(),dict(observe=driver.observe,admit=driver.admit,
            execute=driver.execute,verify_effect=verify,journal=journal,cancelled=lambda:False),clock=lambda:driver.now)
    except Exception as error:
        raise AssertionError('ordinary post-input callback escaped without a receipt') from error
    row=dict(journal_at=journal_at,verify_failure=verify_failure,mutate=mutate,
        result=result,calls=copy.deepcopy(driver.calls),events=events)
    ROWS.append(row);return row


class CompiledCallbackFailureCompositionTests(unittest.TestCase):
    def test_verifier_and_terminal_journal_failures_both_survive(self):
        row=cell('runtime_finished',True);r=row['result']
        self.assertEqual(r['outcome'],'RUNTIME_FAILED');self.assertEqual(r['completed_transitions'],1)
        self.assertTrue(r['transitions'][0]['release_verified'])
        self.assertEqual(r['pending_effect']['action'],'enter')
        names=[e['event'] for e in r['critical_events']]
        self.assertEqual(names.count('journal_write_failed'),1)
        self.assertIn('effect_verification_failed',names)
        self.assertEqual(names[-1],'runtime_finished')
        self.assertEqual(r['critical_events'][-1]['outcome'],'RUNTIME_FAILED')

    def test_terminal_journal_failure_cannot_leave_success_claim(self):
        row=cell('runtime_finished');r=row['result']
        self.assertEqual((r['outcome'],r['reason']),('RUNTIME_FAILED','execution_failed'))
        self.assertEqual(r['completed_transitions'],2)
        self.assertEqual(r['critical_events'][-1]['outcome'],'RUNTIME_FAILED')

    def test_terminal_mutation_then_failure_keeps_private_prefix(self):
        row=cell('action_terminal',mutate=True);r=row['result']
        self.assertEqual(r['completed_transitions'],1)
        self.assertEqual(len(row['calls']['execute']),1);self.assertEqual(len(row['calls']['observe']),1)
        self.assertEqual(row['calls']['verify_effect'],[])
        self.assertEqual(r['critical_events'][-3]['event'],'action_terminal')
        self.assertEqual(row['events'][-1]['event'],'action_terminal')

    def test_mutating_successful_journal_keeps_original_evidence(self):
        row=cell(mutate=True);r=row['result']
        self.assertEqual(r['outcome'],'TASK_SUCCEEDED')
        self.assertEqual(r['completed_transitions'],2)
        self.assertTrue(all(e.get('event') for e in r['critical_events']))

    def test_journal_failure_after_effect_stops_before_next_input(self):
        row=cell('effect_checked');r=row['result']
        self.assertEqual(r['outcome'],'RUNTIME_FAILED');self.assertEqual(r['completed_transitions'],1)
        self.assertEqual(len(row['calls']['execute']),1)
        self.assertEqual(row['events'][-1]['event'],'effect_checked')

    def test_verifier_exception_without_journal_failure_is_typed(self):
        row=cell(verify_failure=True);r=row['result']
        self.assertEqual((r['outcome'],r['reason']),('RUNTIME_FAILED','effect_unavailable'))
        self.assertEqual(r['completed_transitions'],1)

    def test_fatal_verifier_stop_still_propagates_same_object(self):
        driver=fixtures.Driver();stop=BaseException('owned fatal stop')
        def verify(payload):raise stop
        with self.assertRaises(BaseException) as caught:
            compiled_gui.run(fixtures.interface(),dict(observe=driver.observe,admit=driver.admit,
                execute=driver.execute,verify_effect=verify,journal=driver.journal,cancelled=lambda:False),clock=lambda:driver.now)
        self.assertIs(caught.exception,stop);self.assertEqual(len(driver.calls['execute']),1)


if __name__=='__main__':unittest.main()
