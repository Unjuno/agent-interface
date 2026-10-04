"""Actual Xvfb/Xlib boundary: no game, model or consumed producer execution."""
import json
import ast
import queue
import threading
import time
import os
from unittest.mock import patch
from pathlib import Path
import select
import subprocess
import tempfile
import unittest
from Xlib import display
from cleanup import close_resources
from gate import release_gate, fault_gate


class DisplayCleanupBoundary(unittest.TestCase):
    def run_boundary(self, server_first, actual_finally=False, bad_stderr=False, signal_fault=False):
        with tempfile.TemporaryDirectory() as temporary:
            log = (Path(temporary) / 'xvfb.stderr').open('w')
            server = subprocess.Popen(['Xvfb', '-displayfd', '1', '-screen', '0',
                '64x64x24', '-nolisten', 'tcp'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=log, text=True)
            handles = []
            try:
                self.assertTrue(select.select([server.stdout], [], [], 5)[0], 'owned Xvfb startup deadline')
                number = server.stdout.readline().strip()
                self.assertTrue(number.isdigit(), 'owned display identity')
                handles = [display.Display(':' + number), display.Display(':' + number)]
                for handle in handles:
                    self.assertEqual(len(handle.query_keymap()), 32)
                if server_first:
                    server.terminate(); server.wait(timeout=5)
                row = {'cleanup_faults': [], 'scientific_pass': False, 'fatal': None, 'id': 'boundary'}
                output = Path(temporary) / 'RESULT.json'
                faulty = None
                if bad_stderr:
                    faulty = (Path(temporary) / 'faulty.stderr').open('w')
                    faulty.write('buffered output'); os.close(faulty.fileno())
                try:
                    if actual_finally:
                        tree = ast.parse(Path(__file__).with_name('runner.py').read_text())
                        function = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'run_cell')
                        body = next(n for n in function.body if isinstance(n, ast.Try)).finalbody
                        scope = dict(process=server, observer=handles[0], injection_observer=handles[1],
                            result=row, wire=queue.Queue(), reader_thread=None, drain_thread=None,
                            threads=[faulty] if faulty else [], hook=threading.excepthook, unhandled=[], time=time,
                            threading=threading, subprocess=subprocess, cell=Path(temporary),
                            release_gate=release_gate, fault_gate=fault_gate, close_resources=close_resources,
                            write=lambda p, value: p.write_text(json.dumps(value)))
                        compiled = compile(ast.Module(body=body, type_ignores=[]), 'actual-e05-finally', 'exec')
                        if signal_fault:
                            # Only OS signal/wait failure boundaries are injected. The owned
                            # server and clients are real and restored before fixture cleanup.
                            with patch.object(server, 'wait', side_effect=subprocess.TimeoutExpired('owned-Xvfb', 0)), \
                                 patch.object(server, 'terminate', side_effect=PermissionError('terminate denied')), \
                                 patch.object(server, 'kill', side_effect=PermissionError('kill denied')):
                                exec(compiled, scope)
                        else:
                            exec(compiled, scope)
                    else:
                        close_resources(handles, row)
                        output.write_text(json.dumps(row))
                except Exception as exc:
                    self.fail('cleanup prevented result retention: ' + repr(exc))
                decoded = json.loads(output.read_text())
                if actual_finally:
                    self.assertIs(decoded['release_gate'], False)
                self.assertIs(decoded['scientific_pass'], False)
                if signal_fault:
                    self.assertIsNone(decoded['child_exit'])
                    self.assertEqual(sum('PermissionError' in x for x in decoded['cleanup_faults']), 2)
                    self.assertEqual(sum('TimeoutExpired' in x for x in decoded['cleanup_faults']), 3)
                elif server_first:
                    self.assertEqual(len(decoded['cleanup_faults']), 3 if bad_stderr else 2)
                    self.assertEqual(sum('ConnectionClosedError' in x for x in decoded['cleanup_faults']), 2)
                    if bad_stderr:
                        self.assertTrue(any('OSError' in x for x in decoded['cleanup_faults']))
                else:
                    self.assertEqual(decoded['cleanup_faults'], [])
            finally:
                if server.poll() is None:
                    server.terminate(); server.wait(timeout=5)
                server.stdin.close(); server.stdout.close(); log.close()

    def test_closed_server_retains_result_and_both_cleanup_failures(self):
        self.run_boundary(True)

    def test_clients_close_before_server_without_cleanup_failure(self):
        self.run_boundary(False)

    def test_actual_runner_finally_retains_result_after_dead_display(self):
        self.run_boundary(True, actual_finally=True)

    def test_actual_runner_finally_retains_result_after_real_bad_stderr_close(self):
        self.run_boundary(True, actual_finally=True, bad_stderr=True)

    def test_actual_runner_finally_retains_result_after_signal_and_wait_failures(self):
        self.run_boundary(False, actual_finally=True, signal_fault=True)


if __name__ == '__main__':
    unittest.main()
