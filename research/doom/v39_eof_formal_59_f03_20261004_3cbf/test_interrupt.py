"""Real SIGINT after a child exists: cleanup and terminal STOP must survive."""
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import unittest


class InterruptControl(unittest.TestCase):
    def test_row_file_write_failure_leaves_external_journal_record(self):
        with tempfile.TemporaryDirectory() as name:
            output = Path(name) / 'output'
            code = (
                'import sys; import runner; original=runner.write\n'
                'def write(path,value):\n'
                ' if path.name=="baseline_eof.json": raise OSError("injected row storage failure")\n'
                ' original(path,value)\n'
                'runner.write=write\n'
                'runner.run(__import__("pathlib").Path(sys.argv[1]),journal=sys.stdout)\n')
            process = subprocess.run([sys.executable, '-B', '-c', code, str(output)],
                                     capture_output=True, text=True)
            self.assertNotEqual(process.returncode, 0)
            records = [line for line in process.stdout.splitlines() if line.startswith('F03_CELL_RECORD ')]
            self.assertEqual(len(records), 1)
            row = json.loads(records[0].removeprefix('F03_CELL_RECORD '))
            self.assertEqual(row['case'], 'baseline_eof')
            self.assertTrue(row['gate'])
            self.assertIn('injected row storage failure', process.stderr)
            self.assertFalse((output / 'SUMMARY.json').exists())

    def test_sigint_after_child_start_retains_stop(self):
        with tempfile.TemporaryDirectory() as name:
            output = Path(name) / 'output'
            process = subprocess.Popen([sys.executable, '-B', str(Path(__file__).with_name('runner.py')), str(output)],
                                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            try:
                deadline = time.monotonic() + 3
                children = []
                while time.monotonic() < deadline and process.poll() is None:
                    proc_children = Path('/proc') / str(process.pid) / 'task' / str(process.pid) / 'children'
                    if proc_children.exists():
                        children = [int(value) for value in proc_children.read_text().split()]
                    else:
                        listing = subprocess.check_output(['ps', '-axo', 'ppid=,pid='], text=True)
                        children = [int(line.split()[1]) for line in listing.splitlines()
                                    if line.split() and int(line.split()[0]) == process.pid]
                    if children:
                        break
                    time.sleep(.01)
                self.assertTrue(children, 'no actual child observed before interrupt')
                os.kill(process.pid, signal.SIGINT)
                stdout, stderr = process.communicate(timeout=5)
                self.assertEqual(process.returncode, 1, stderr)
                self.assertTrue((output / 'SUMMARY.json').exists(), stderr)
                summary = json.loads((output / 'SUMMARY.json').read_text())
                self.assertEqual(summary['cases'], ['baseline_eof'])
                self.assertEqual(summary['verdict'], 'STOP_FIRST_UNEXPECTED_CELL')
                self.assertEqual(summary['stop_reason'], 'KeyboardInterrupt')
                row = json.loads((output / 'baseline_eof.json').read_text())
                self.assertIs(row['cleanup_child_alive'], False)
                # None is explicitly emitted only when no reader was created.
                self.assertIn(row['cleanup_reader_alive'], (False, None))
                self.assertEqual(row['cleanup_faults'], [])
            finally:
                if process.poll() is None:
                    process.kill(); process.wait(timeout=3)
                process.stdout.close(); process.stderr.close()

    def test_sigint_during_cell_write_still_retains_row_and_stop_summary(self):
        with tempfile.TemporaryDirectory() as name:
            output = Path(name) / 'output'
            code = (
                'import os,signal,sys; import runner; original=runner.write\n'
                'def write(path,value):\n'
                ' original(path,value)\n'
                ' if path.name=="baseline_eof.json": os.kill(os.getpid(),signal.SIGINT)\n'
                'runner.write=write\n'
                'sys.exit(runner.run(__import__("pathlib").Path(sys.argv[1])))\n')
            process = subprocess.run([sys.executable, '-B', '-c', code, str(output)],
                                     capture_output=True, text=True)
            self.assertNotEqual(process.returncode, 0)
            self.assertTrue((output / 'baseline_eof.json').exists(), process.stderr)
            self.assertTrue((output / 'SUMMARY.json').exists(), process.stderr)
            summary = json.loads((output / 'SUMMARY.json').read_text())
            self.assertEqual(summary['cases'], ['baseline_eof'])
            self.assertIn('STOP', summary['verdict'])

    def test_sigint_at_finalize_entry_retains_reaped_child_and_stop(self):
        with tempfile.TemporaryDirectory() as name:
            output = Path(name) / 'output'
            code = (
                'import os,signal,sys; import runner; original=runner.finalize_cell\n'
                'def interrupt_before_finalize(*args):\n'
                ' os.kill(os.getpid(),signal.SIGINT)\n'
                ' original(*args)\n'
                'runner.finalize_cell=interrupt_before_finalize\n'
                'sys.exit(runner.run(__import__("pathlib").Path(sys.argv[1])))\n')
            process = subprocess.run([sys.executable, '-B', '-c', code, str(output)],
                                     capture_output=True, text=True)
            self.assertEqual(process.returncode, 1, process.stderr)
            row = json.loads((output / 'baseline_eof.json').read_text())
            self.assertIs(row['cleanup_child_alive'], False)
            self.assertFalse(row['cleanup_faults'])
            summary = json.loads((output / 'SUMMARY.json').read_text())
            self.assertEqual(summary['cases'], ['baseline_eof'])
            self.assertEqual(summary['verdict'], 'STOP_FIRST_UNEXPECTED_CELL')
            self.assertEqual(summary['stop_reason'], 'KeyboardInterrupt')
