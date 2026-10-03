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
                self.assertIs(row['cleanup_reader_alive'], False)
                self.assertEqual(row['cleanup_faults'], [])
            finally:
                if process.poll() is None:
                    process.kill(); process.wait(timeout=3)
                process.stdout.close(); process.stderr.close()
