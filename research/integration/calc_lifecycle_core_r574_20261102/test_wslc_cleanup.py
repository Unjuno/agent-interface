import json
import subprocess
import unittest
from unittest.mock import patch

from wslc_cleanup import cleanup_owned

CID = 'a' * 64
RUN = 'b' * 32
LABEL = 'agent-interface.run-id'


def response(args, *, code=0, out=b'', err=b''):
    return subprocess.CompletedProcess(args, code, out, err)


def inspect(cid=CID, run=RUN, running=True):
    return json.dumps([{'Id': cid, 'Config': {'Labels': {LABEL: run}},
                        'State': {'Running': running}}]).encode()


def row(cid=CID, run=RUN):
    return json.dumps({'ID': cid, 'Labels': LABEL + '=' + run}).encode() + b'\n'


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
        with patch('wslc_cleanup.time.monotonic', side_effect=[0, 0, 2]):
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
    def test_expired_budget_never_calls_cli(self):
        runner = Runner([])
        self.assertEqual(cleanup_owned(CID, RUN, timeout_s=0, runner=runner)['status'], 'UNKNOWN')
        self.assertEqual(runner.calls, [])


if __name__ == '__main__':
    unittest.main()
