import json
from pathlib import Path
import queue
import subprocess
import sys
import tarfile
import threading
import unittest
from candidate import factory


class RealPipeBoundary(unittest.TestCase):
    def exercise(self, wire, first_event=None, waits=1, callback_fault=False):
        archive = Path(__file__).parent.parent / 'v39_native_fault_59_e05_20261004_3cbf/source-closure.tar.gz'
        with tarfile.open(archive, 'r:gz') as source:
            code = source.extractfile('research/doom/v39_reader_signal_59_e02_20261004_3cbf/source/v39-candidate.py.txt').read()
        child = subprocess.Popen([sys.executable, '-u', '-c',
            'import os,sys,time;sys.stdout.write(sys.argv[1]);sys.stdout.flush();os.close(1);time.sleep(3)', wire],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        thread = None
        try:
            reader, wait, events = factory(code)(child, queue.Queue())
            thread = threading.Thread(target=reader); thread.start(); thread.join(1)
            self.assertFalse(thread.is_alive()); self.assertIsNone(child.poll())
            if callback_fault:
                unrelated = type('_SessionReaderFailure', (RuntimeError,), {})
                def faulty_predicate(row):
                    raise unrelated('callback error, not reader failure')
                with self.assertRaises(unrelated):
                    wait(faulty_predicate, timeout=.1)
            if first_event:
                self.assertEqual(wait(lambda row: row['event'] == first_event, timeout=.1), {'event': first_event})
            for attempt in range(waits):
                try:
                    wait(lambda row: False, timeout=.1)
                except Exception as error:
                    self.assertEqual(type(error).__name__, '_SessionReaderFailure', f'wait attempt {attempt + 1}')
                    self.assertIsInstance(error.__cause__, json.JSONDecodeError if wire == 'not-json\n' else EOFError)
                else:
                    self.fail('ended pipe not signalled')
        finally:
            child.terminate()
            try:
                child.wait(timeout=2)
            except subprocess.TimeoutExpired:
                child.kill(); child.wait(timeout=2)
            child.stdout.close(); child.stderr.close()
            if thread is not None:
                thread.join(1)
                self.assertFalse(thread.is_alive())

    def test_live_child_empty_eof_not_silent_timeout(self):
        self.exercise('')

    def test_ready_precedes_eof_failure(self):
        self.exercise('{"event":"ready"}\n', 'ready')

    def test_terminal_precedes_eof_failure(self):
        self.exercise('{"event":"terminal"}\n', 'terminal')

    def test_parser_cause_not_replaced_with_eof(self):
        self.exercise('not-json\n')

    def test_repeated_wait_does_not_lose_eof_state(self):
        self.exercise('', waits=2)

    def test_repeated_wait_does_not_lose_parser_failure(self):
        self.exercise('not-json\n', waits=2)

    def test_same_named_callback_error_does_not_block_queued_terminal(self):
        self.exercise('{"event":"ready"}\n{"event":"terminal"}\n', 'terminal', callback_fault=True)
