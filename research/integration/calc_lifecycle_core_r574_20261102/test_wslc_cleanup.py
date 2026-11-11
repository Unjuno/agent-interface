import json
import subprocess
import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch

from wslc_cleanup import cleanup_owned

CID = 'a' * 64
RUN = 'b' * 32
LABEL = 'agent-interface.run-id'


def response(args, *, code=0, out=b'', err=b''):
    return subprocess.CompletedProcess(args, code, out, err)


def inspect(cid=CID, run=RUN, running=True, exit_code=7):
    return json.dumps([{'Id': cid, 'Config': {'Labels': {LABEL: run}},
                        'State': {'Running': running, 'Status': 'running' if running else 'exited', 'ExitCode': exit_code}}]).encode()


def row(cid=CID, run=RUN, state='running'):
    return json.dumps({'ID': cid, 'Labels': LABEL + '=' + run, 'State': state}).encode() + b'\n'


class Runner:
    def __init__(self, answers):
        self.answers = iter(answers)
        self.calls = []
    def __call__(self, args, timeout):
        self.calls.append((args, timeout))
        answer = next(self.answers)
        if isinstance(answer, BaseException):
            raise answer
        return response(args, **answer)


def remove_with_journal(runner):
    with tempfile.TemporaryDirectory() as directory:
        return cleanup_owned(CID, RUN, runner=runner, remove_exited=True,
                             journal_path=Path(directory) / 'cleanup.jsonl')


class CleanupTests(unittest.TestCase):
    def test_invalid_identity_never_calls_cli(self):
        for cid, run in [('', RUN), ('a' * 63, RUN), (CID.upper(), RUN), (CID, '')]:
            runner = Runner([])
            self.assertEqual(cleanup_owned(cid, run, runner=runner)['status'], 'UNKNOWN')
            self.assertEqual(runner.calls, [])

    def test_inspect_failure_or_mismatch_never_stops(self):
        for answer in [{'code': 1}, {'out': b'invalid'}, {'out': inspect(run='c'*32)},
                       {'out': inspect(cid='c'*64)}, {'out': inspect(running='true')},
                       subprocess.TimeoutExpired('wslc', 1)]:
            runner = Runner([answer])
            self.assertEqual(cleanup_owned(CID, RUN, runner=runner)['status'], 'UNKNOWN')
            self.assertEqual(len(runner.calls), 1)

    def test_bad_pre_list_never_stops(self):
        for answer in [{'code': 1}, {'out': b''}, {'out': row(cid='c'*64)},
                       {'out': row()+row()}, {'out': b'bad'}]:
            runner = Runner([{'out': inspect()}, answer])
            self.assertEqual(cleanup_owned(CID, RUN, runner=runner)['status'], 'UNKNOWN')
            self.assertEqual(len(runner.calls), 2)

    def test_verified_stop_then_empty_list(self):
        runner = Runner([{'out': inspect()}, {'out': row()},
                         {'out': (CID + '\n').encode()}, {'out': b''}])
        result = cleanup_owned(CID, RUN, runner=runner)
        self.assertEqual(result['status'], 'observed_absent')
        self.assertEqual(len(result['commands']), 4)
        self.assertEqual(runner.calls[2][0][-1], CID)

    def test_stop_or_postcheck_failure_stays_unknown(self):
        for stop, post in [({'code': 1}, None), ({'out': b'other\n'}, None),
                           ({'out': (CID+'\n').encode()}, {'code': 1}),
                           ({'out': (CID+'\n').encode()}, {'out': row()})]:
            answers = [{'out': inspect()}, {'out': row()}, stop]
            if post is not None: answers.append(post)
            self.assertEqual(cleanup_owned(CID, RUN, runner=Runner(answers))['status'], 'UNKNOWN')

    def test_deadline_after_inspect_prevents_list(self):
        runner = Runner([{'out': inspect()}])
        with patch('wslc_cleanup.time.monotonic', side_effect=[0, 0, 0, 2]):
            result = cleanup_owned(CID, RUN, timeout_s=1, runner=runner)
        self.assertEqual(result['status'], 'UNKNOWN')
        self.assertEqual(len(runner.calls), 1)

    def test_stop_timeout_retains_partial_output_and_does_not_list(self):
        import base64
        timeout = subprocess.TimeoutExpired('wslc', 1, output=b'partial', stderr=b'error')
        runner = Runner([{'out': inspect()}, {'out': row()}, timeout])
        result = cleanup_owned(CID, RUN, runner=runner)
        self.assertEqual(result['status'], 'UNKNOWN')
        self.assertEqual(len(runner.calls), 3)
        self.assertEqual(base64.b64decode(result['commands'][-1]['stdout_b64']), b'partial')
        self.assertEqual(base64.b64decode(result['commands'][-1]['stderr_b64']), b'error')
    def test_interruption_keeps_stop_intent_in_durable_journal(self):
        with tempfile.TemporaryDirectory() as directory:
            journal = Path(directory) / 'cleanup.jsonl'
            runner = Runner([{'out': inspect()}, {'out': row()}, KeyboardInterrupt()])
            with self.assertRaises(KeyboardInterrupt):
                cleanup_owned(CID, RUN, runner=runner, journal_path=journal)
            events = [json.loads(line) for line in journal.read_text().splitlines()]
            self.assertEqual(events[-1]['event'], 'command_interrupted')
            self.assertEqual(events[-1]['error_type'], 'KeyboardInterrupt')
            self.assertEqual(events[-2]['event'], 'command_started')
            self.assertEqual(events[-2]['argv'][-1], CID)
            self.assertIn('stop', events[-2]['argv'])

    def test_journal_failure_before_stop_prevents_stop(self):
        with tempfile.TemporaryDirectory() as directory:
            journal = Path(directory) / 'cleanup.jsonl'
            runner = Runner([{'out': inspect()}, {'out': row()}])
            # Four fsyncs record inspect/list intent and return; the fifth is stop intent.
            with patch('wslc_cleanup.os.fsync', side_effect=[None, None, None, None, OSError('disk')]):
                with self.assertRaises(OSError):
                    cleanup_owned(CID, RUN, runner=runner, journal_path=journal)
            self.assertEqual(len(runner.calls), 2)

    def test_journal_return_failure_is_not_reported_as_cli_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            journal = Path(directory) / 'cleanup.jsonl'
            runner = Runner([{'out': inspect()}])
            with patch('wslc_cleanup.os.fsync', side_effect=[None, OSError('disk')]):
                with self.assertRaises(OSError):
                    cleanup_owned(CID, RUN, runner=runner, journal_path=journal)
            self.assertEqual(len(runner.calls), 1)
            events = [json.loads(line) for line in journal.read_text().splitlines()]
            self.assertNotIn('command_failed', [event['event'] for event in events])

    def test_journal_contains_final_result_on_normal_return(self):
        with tempfile.TemporaryDirectory() as directory:
            journal = Path(directory) / 'cleanup.jsonl'
            runner = Runner([{'out': inspect(running=False)}, {'out': row(state='exited')}])
            result = cleanup_owned(CID, RUN, runner=runner, journal_path=journal)
            events = [json.loads(line) for line in journal.read_text().splitlines()]
            self.assertEqual(events[-1]['event'], 'result')
            self.assertEqual(events[-1]['receipt'], result)

    def test_stopped_owned_target_is_observed_but_not_stopped(self):
        runner = Runner([{'out': inspect(running=False)}, {'out': row(state='exited')}])
        result = cleanup_owned(CID, RUN, runner=runner)
        self.assertEqual(result['status'], 'observed_stopped')
        self.assertEqual(len(runner.calls), 2)

    def test_stale_stopped_inspect_does_not_claim_stopped(self):
        runner = Runner([{'out': inspect(running=False)}, {'out': row(state='running')}])
        self.assertEqual(cleanup_owned(CID, RUN, runner=runner)['status'], 'UNKNOWN')
        self.assertEqual(len(runner.calls), 2)

    def test_deadline_after_intent_does_not_invoke_command(self):
        with tempfile.TemporaryDirectory() as directory:
            journal = Path(directory) / 'cleanup.jsonl'
            runner = Runner([])
            with patch('wslc_cleanup.time.monotonic', side_effect=[0, 0, 2]):
                result = cleanup_owned(CID, RUN, timeout_s=1, runner=runner, journal_path=journal)
            self.assertEqual(result['status'], 'UNKNOWN')
            self.assertEqual(runner.calls, [])
            events = [json.loads(line) for line in journal.read_text().splitlines()]
            self.assertEqual(events[1]['event'], 'command_not_invoked')

    def test_exited_receipt_is_retained_before_exact_removal(self):
        with tempfile.TemporaryDirectory() as directory:
            journal = Path(directory) / 'cleanup.jsonl'
            runner = Runner([{'out': inspect(running=False)}, {'out': row(state='exited')},
                             {'out': (CID+'\n').encode()}, {'out': b''}])
            result = cleanup_owned(CID, RUN, runner=runner, journal_path=journal, remove_exited=True)
            self.assertEqual(result['status'], 'observed_absent')
            self.assertEqual(result['observed_exit_code'], 7)
            self.assertEqual(runner.calls[2][0], ['wslc', 'container', 'remove', CID])
            events = [json.loads(line) for line in journal.read_text().splitlines()]
            self.assertLess(next(i for i,e in enumerate(events) if e['event']=='exit_observed'),
                            next(i for i,e in enumerate(events) if e['event']=='command_started' and 'remove' in e['argv']))

    def test_remove_requires_exclusive_journal(self):
        runner = Runner([])
        with self.assertRaises(ValueError):
            cleanup_owned(CID, RUN, runner=runner, remove_exited=True)
        self.assertEqual(runner.calls, [])

    def test_exit_receipt_requires_valid_exited_state(self):
        for code in (None, True, '7'):
            runner = Runner([{'out': inspect(running=False, exit_code=code)}, {'out': row(state='exited')}])
            result = remove_with_journal(runner)
            self.assertEqual(result['status'], 'UNKNOWN')
            self.assertNotIn('observed_exit_code', result)
            self.assertLessEqual(len(runner.calls), 2)

    def test_failed_remove_keeps_exit_observation_but_not_absence(self):
        runner = Runner([{'out': inspect(running=False)}, {'out': row(state='exited')}, {'code': 1}])
        result = remove_with_journal(runner)
        self.assertEqual(result['status'], 'UNKNOWN')
        self.assertEqual(result['observed_exit_code'], 7)

    def test_exit_evidence_sync_failure_prevents_remove(self):
        with tempfile.TemporaryDirectory() as directory:
            journal = Path(directory) / 'cleanup.jsonl'
            runner = Runner([{'out': inspect(running=False)}, {'out': row(state='exited')}])
            # Inspect and list each write intent and return; the fifth sync is exit evidence.
            with patch('wslc_cleanup.os.fsync', side_effect=[None, None, None, None, OSError('disk')]):
                with self.assertRaises(OSError):
                    cleanup_owned(CID, RUN, runner=runner, journal_path=journal, remove_exited=True)
            self.assertEqual(len(runner.calls), 2)

    def test_deadline_during_exit_sync_prevents_remove(self):
        with tempfile.TemporaryDirectory() as directory:
            journal = Path(directory) / 'cleanup.jsonl'
            runner = Runner([{'out': inspect(running=False)}, {'out': row(state='exited')}])
            clock = {'now': 0, 'syncs': 0}
            def sync(_):
                clock['syncs'] += 1
                if clock['syncs'] == 5:
                    clock['now'] = 2
            with patch('wslc_cleanup.os.fsync', side_effect=sync), \
                 patch('wslc_cleanup.time.monotonic', side_effect=lambda: clock['now']):
                result = cleanup_owned(CID, RUN, runner=runner, journal_path=journal,
                                       remove_exited=True, timeout_s=1)
            self.assertEqual(result['status'], 'UNKNOWN')
            self.assertEqual(result['observed_exit_code'], 7)
            self.assertEqual(len(runner.calls), 2)

    def test_remove_timeout_retains_partial_output_and_exit_evidence(self):
        import base64
        timeout = subprocess.TimeoutExpired('wslc', 1, output=b'partial')
        runner = Runner([{'out': inspect(running=False)}, {'out': row(state='exited')}, timeout])
        result = remove_with_journal(runner)
        self.assertEqual(result['status'], 'UNKNOWN')
        self.assertEqual(result['observed_exit_code'], 7)
        self.assertEqual(base64.b64decode(result['commands'][-1]['stdout_b64']), b'partial')
        self.assertEqual(len(runner.calls), 3)

    def test_remove_success_without_empty_post_list_stays_unknown(self):
        runner = Runner([{'out': inspect(running=False)}, {'out': row(state='exited')},
                         {'out': (CID+'\n').encode()}, {'out': row(state='exited')}])
        result = remove_with_journal(runner)
        self.assertEqual(result['status'], 'UNKNOWN')
        self.assertEqual(result['observed_exit_code'], 7)
        self.assertTrue(result['remove_command_succeeded'])

    def test_running_target_is_never_removed_by_exited_mode(self):
        runner = Runner([{'out': inspect()}, {'out': row()}])
        result = remove_with_journal(runner)
        self.assertEqual(result['status'], 'UNKNOWN')
        self.assertEqual(len(runner.calls), 2)

    def test_existing_journal_prevents_any_command(self):
        with tempfile.TemporaryDirectory() as directory:
            journal = Path(directory) / 'cleanup.jsonl'
            journal.write_text('previous')
            runner = Runner([])
            with self.assertRaises(FileExistsError):
                cleanup_owned(CID, RUN, runner=runner, journal_path=journal)
            self.assertEqual(runner.calls, [])
            self.assertEqual(journal.read_text(), 'previous')

    def test_expired_budget_never_calls_cli(self):
        runner = Runner([])
        self.assertEqual(cleanup_owned(CID, RUN, timeout_s=0, runner=runner)['status'], 'UNKNOWN')
        self.assertEqual(runner.calls, [])


if __name__ == '__main__':
    unittest.main()
