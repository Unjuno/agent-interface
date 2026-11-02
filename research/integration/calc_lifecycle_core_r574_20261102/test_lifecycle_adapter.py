"""Fake WSLc transport composed with the real Windows JobHost process owner."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from lifecycle_adapter import WslcLifecycleAdapter
from lifecycle_launcher import run_attempt

RUN = 'b' * 32
CID = 'a' * 64
IMAGE = 'sha256:' + '1' * 64


class FakeWslc:
    def __init__(self, output, *, fail_start=False, bad_filter=False, neutral_input=True):
        self.output = Path(output)
        self.fail_start = fail_start
        self.bad_filter = bad_filter
        self.neutral_input = neutral_input
        self.removed = False
        self.calls = []

    def _state(self, *, running=False):
        return json.dumps([{
            'Id': CID,
            'Config': {'Labels': {'agent-interface.run-id': RUN}},
            'State': {'Running': running,
                      'Status': 'running' if running else 'exited',
                      'ExitCode': 0},
        }]).encode('ascii')

    def __call__(self, args, timeout):
        self.calls.append(args)
        if args[1] == 'run':
            if self.fail_start:
                raise subprocess.TimeoutExpired(args, timeout, output=b'partial')
            cidfile = Path(args[args.index('--cidfile') + 1])
            cidfile.write_text(CID, encoding='ascii')
            mount = args[args.index('--mount') + 1]
            source = next(x[7:] for x in mount.split(',') if x.startswith('source='))
            (Path(source) / 'task-effect.txt').write_text('472/615\n', encoding='ascii')
            (Path(source) / 'input-release.json').write_text(json.dumps({
                'source': 'test-only-synthetic-readback',
                'keys_down': [] if self.neutral_input else ['w'],
            }), encoding='ascii')
            return subprocess.CompletedProcess(args, 0, CID.encode(), b'swap not limited')
        if args[1:3] == ['container', 'inspect']:
            return subprocess.CompletedProcess(args, 0, self._state(running=self.calls.count(args) == 1), b'')
        if args[1:3] == ['container', 'list']:
            if self.removed:
                out = b''
            else:
                returned_cid = ('c' * 64) if self.bad_filter else CID
                out = json.dumps({'ID': returned_cid, 'State': 'exited'}).encode('ascii') + b'\n'
            return subprocess.CompletedProcess(args, 0, out, b'')
        if args[1:3] == ['container', 'stop']:
            return subprocess.CompletedProcess(args, 0, CID.encode(), b'')
        if args[1:3] == ['container', 'remove']:
            self.removed = True
            return subprocess.CompletedProcess(args, 0, CID.encode(), b'')
        raise AssertionError('unexpected WSLc command: ' + repr(args))


class LifecycleAdapterValidationTests(unittest.TestCase):
    def test_cleanup_requires_final_exact_id_absence_not_stale_stop_receipt(self):
        class ReappearedContainer:
            def reconcile(self, *, timeout_s):
                return {
                    'stop': {'status': 'observed_absent'},
                    'stop_returned_late': False,
                    'remove': {'status': 'UNKNOWN', 'observed_running': True},
                    'remove_returned_late': False,
                }

        adapter = WslcLifecycleAdapter(
            host_argv=[sys.executable, '-c', 'pass'],
            image=IMAGE, container_command=['python3', '-c', 'pass'],
            audit=lambda root: {'status': 'failed'},
        )
        result = adapter.cleanup_container(ReappearedContainer(), 1)
        self.assertEqual(result['status'], 'UNKNOWN')

    def test_mounts_cannot_escape_or_expose_the_attempt_root(self):
        for mount_path_kind in ('outside', 'root'):
            with self.subTest(mount_path=mount_path_kind), tempfile.TemporaryDirectory() as temp:
                parent = Path(temp)
                allocation = parent / 'attempt'
                allocation.mkdir()
                (allocation / 'conditions.json').write_text(
                    json.dumps({'run_id': RUN}), encoding='utf-8')
                outside = parent / 'outside'
                outside.mkdir()
                mount_path = outside if mount_path_kind == 'outside' else allocation
                runner = FakeWslc(outside)
                adapter = WslcLifecycleAdapter(
                    host_argv=[sys.executable, '-c', 'pass'],
                    image=IMAGE, container_command=['python3', '-c', 'pass'],
                    audit=lambda root: {'status': 'failed'},
                    mounts={'/out': (mount_path, False)}, runner=runner,
                )
                with self.assertRaisesRegex(ValueError, 'mount'):
                    adapter.prepare_container(allocation)
                self.assertEqual(runner.calls, [])


@unittest.skipUnless(sys.platform == 'win32', 'real JobHost process composition requires Windows')
class LifecycleAdapterTests(unittest.TestCase):
    def _run(self, *, host_code='pass', fail_start=False, bad_filter=False,
             neutral_input=True):
        with tempfile.TemporaryDirectory() as temp:
            allocation = Path(temp) / 'attempt'
            output = allocation / 'container' / 'out'
            audit_rows = []

            def audit(root):
                effect = (root / 'container' / 'out' / 'task-effect.txt').read_text(encoding='ascii')
                release = json.loads((root / 'container' / 'out' / 'input-release.json').read_text(encoding='ascii'))
                audit_rows.append(effect)
                return {'status': 'passed' if effect == '472/615\n' else 'failed',
                        'release_confirmed': (release.get('source') == 'test-only-synthetic-readback'
                                              and release.get('keys_down') == [])}

            runner = FakeWslc(output, fail_start=fail_start, bad_filter=bad_filter,
                              neutral_input=neutral_input)
            adapter = WslcLifecycleAdapter(
                host_argv=[sys.executable, '-c', host_code],
                image=IMAGE, container_command=['python3', '-c', 'pass'],
                audit=audit,
                mounts={'/out': (output, False)},
                runner=runner,
            )
            result = run_attempt(allocation, {'run_id': RUN}, adapter, timeout_s=10)
            return result, runner, audit_rows

    def test_composes_host_container_cleanup_and_independent_task_audit(self):
        result, runner, audit_rows = self._run()
        self.assertEqual(result['status'], 'completed_scoped')
        self.assertEqual(result['host']['exit_code'], 0)
        self.assertEqual(result['host']['retirement']['status'], 'closed_scoped')
        self.assertEqual(result['container']['exit_code'], 0)
        self.assertEqual(result['cleanup']['status'], 'confirmed')
        self.assertEqual(result['audit']['status'], 'passed')
        self.assertEqual(result['input_release'], 'confirmed')
        self.assertEqual(audit_rows, ['472/615\n'])
        self.assertTrue(runner.removed)

    def test_container_start_timeout_stays_incomplete_and_cleans_host(self):
        result, runner, audit_rows = self._run(fail_start=True)
        self.assertEqual(result['status'], 'incomplete')
        self.assertEqual(result['container']['status'], 'unknown')
        self.assertEqual(result['cleanup']['status'], 'UNKNOWN')
        self.assertEqual(result['host']['exit_code'], 0)
        self.assertEqual(result['audit']['status'], 'not_run')
        self.assertEqual(audit_rows, [])
        self.assertEqual(len(runner.calls), 1)

    def test_wrong_exact_id_filter_stays_cleanup_unknown(self):
        result, runner, _ = self._run(bad_filter=True)
        self.assertEqual(result['status'], 'incomplete')
        self.assertEqual(result['container']['exit_code'], 0)
        self.assertEqual(result['cleanup']['status'], 'UNKNOWN')
        self.assertEqual(result['input_release'], 'confirmed')
        self.assertFalse(runner.removed)

    def test_host_nonzero_exit_and_unknown_release_are_not_promoted(self):
        result, _, _ = self._run(host_code='raise SystemExit(4)', neutral_input=False)
        self.assertEqual(result['status'], 'incomplete')
        self.assertEqual(result['host']['status'], 'exited')
        self.assertEqual(result['host']['exit_code'], 4)
        self.assertEqual(result['input_release'], 'UNKNOWN')


if __name__ == '__main__':
    unittest.main()
