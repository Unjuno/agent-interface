"""Owned ordinary OS-pipe regressions; no Codex or peer producer execution."""
import base64
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import time
import unittest

from codex_app_server_client_v2 import CodexAppServerClient


FRAME = {'method': 'owned/late-frame', 'params': {'marker': 'reader-retirement-v2'}}
WRITER = '''import json, os, sys
from pathlib import Path
ready = Path(sys.argv[1])
with ready.open('xb'):
    pass
if sys.stdin.readline() != 'release\\n':
    raise RuntimeError('owned writer release missing')
print(json.dumps({'method':'owned/late-frame','params':{'marker':'reader-retirement-v2'}}, separators=(',', ':')), flush=True)
'''


class ReaderRetirementTests(unittest.TestCase):
    def save(self, record):
        location = os.environ.get('JOURNAL_CLOSE_EVIDENCE_DIR')
        if location is not None:
            target = Path(location) / (self._testMethodName + '.json')
            with target.open('x', encoding='utf-8') as stream:
                json.dump(dict(record, method=self._testMethodName), stream, indent=2)
                stream.write('\n')

    def pipe_case(self, held, journal_enabled):
        with tempfile.TemporaryDirectory(prefix='reader-retirement-owned-') as temporary:
            home = Path(temporary)
            journal = home / 'journal.jsonl'
            ready = home / 'writer-ready'
            rfd, wfd = os.pipe()
            reader_stream = os.fdopen(rfd, 'r', encoding='utf-8', newline='')
            parent = writer = client = caller = None
            record = {'kind': 'new-owned-parent-plus-independent-writer-pipe',
                      'held_writer': held, 'journal_enabled': journal_enabled,
                      'configured_close_seconds': 0.05, 'observation_checkpoint_seconds': 0.5,
                      'native_handles': [], 'reader_errors': [], 'first_outcome': {}}
            original_hook = threading.excepthook
            def capture(error):
                if client is not None and error.thread is client._reader:
                    record['reader_errors'].append({'type': error.exc_type.__name__,
                                                   'message': str(error.exc_value)})
                else:
                    original_hook(error)
            done = threading.Event()
            def close_once():
                result = record['first_outcome']
                result['start_ns'] = time.monotonic_ns()
                try:
                    result['return_value'] = client.close(timeout=0.05)
                except BaseException as error:
                    result['error_type'] = type(error).__name__
                    result['error_message'] = str(error)
                finally:
                    result['end_ns'] = time.monotonic_ns()
                    done.set()
            def launch(argv, **kwargs):
                from datetime import datetime, timezone
                started = datetime.now(timezone.utc).isoformat()
                process = subprocess.Popen(argv, **kwargs)
                record['native_handles'].append({'argv': argv, 'pid': process.pid,
                    'spawn_started_utc': started, 'spawn_returned_utc': datetime.now(timezone.utc).isoformat()})
                return process
            try:
                parent = launch([sys.executable, '-B', '-u', '-c', 'pass'],
                                stdin=subprocess.PIPE, stdout=wfd, stderr=subprocess.PIPE, text=True)
                parent.stdout = reader_stream
                if held:
                    writer = launch([sys.executable, '-B', '-u', '-c', WRITER, str(ready)],
                                    stdin=subprocess.PIPE, stdout=wfd, stderr=subprocess.PIPE, text=True)
                os.close(wfd)
                wfd = None
                parent.wait(timeout=2)
                record['parent_exit_before_close'] = parent.returncode
                if held:
                    deadline = time.monotonic() + 2
                    while not ready.exists() and time.monotonic() < deadline and writer.poll() is None:
                        time.sleep(0.005)
                    if not ready.exists():
                        raise AssertionError('owned writer did not become ready')
                    record['writer_ready_bytes'] = ready.stat().st_size
                    record['writer_exit_before_close'] = writer.poll()
                def factory(_command, **_kwargs):
                    return parent
                client = CodexAppServerClient(['owned-prestarted-pipe'], process_factory=factory,
                                              journal_path=journal if journal_enabled else None)
                threading.excepthook = capture
                if not held:
                    client._reader.join(timeout=2)
                caller = threading.Thread(target=close_once)
                caller.start()
                record['close_done_at_checkpoint'] = done.wait(0.5)
                record['first_checkpoint_ns'] = time.monotonic_ns()
                record['reader_alive_at_checkpoint'] = client._reader.is_alive()
                record['journal_closed_at_checkpoint'] = None if client._journal is None else client._journal.closed
                record['journal_lock_locked_at_checkpoint'] = client._journal_lock.locked()
                record['journal_before_release_base64'] = None if not journal_enabled else base64.b64encode(journal.read_bytes()).decode()
            finally:
                # Release only our writer and reap only our actual process handles, even on first failure.
                if writer is not None:
                    if writer.poll() is None:
                        try:
                            writer.stdin.write('release\n')
                            writer.stdin.flush()
                        except (BrokenPipeError, OSError):
                            pass
                    try:
                        writer.wait(timeout=2)
                    except subprocess.TimeoutExpired:
                        record['driver_writer_kill_required'] = True
                        writer.kill()
                        writer.wait(timeout=2)
                    record['writer_final_exit'] = writer.returncode
                    record['writer_stderr_base64'] = base64.b64encode(writer.stderr.read().encode()).decode()
                if wfd is not None:
                    os.close(wfd)
                if client is not None:
                    client._reader.join(timeout=2)
                    if caller is not None:
                        caller.join(timeout=2)
                    record['reader_alive_after_release'] = client._reader.is_alive()
                    record['caller_alive_after_release'] = False if caller is None else caller.is_alive()
                    with client._condition:
                        record['actual_notifications'] = list(client._notifications)
                        record['actual_responses'] = dict(client._responses)
                        record['actual_client_closed'] = client._closed
                    record['second_close'] = {}
                    if not client._reader.is_alive() and (caller is None or not caller.is_alive()):
                        try:
                            record['second_close']['return_value'] = client.close(timeout=0.1)
                        except BaseException as error:
                            record['second_close']['error_type'] = type(error).__name__
                    record['journal_final_closed'] = None if client._journal is None else client._journal.closed
                    record['journal_final_base64'] = None if not journal_enabled else base64.b64encode(journal.read_bytes()).decode()
                threading.excepthook = original_hook
                if parent is not None:
                    if parent.poll() is None:
                        parent.kill()
                        parent.wait(timeout=2)
                        record['driver_parent_kill_required'] = True
                    record['parent_final_exit'] = parent.returncode
                    if parent.stderr.closed:
                        snapshot = client.stderr_snapshot()
                        record['parent_stderr_capture'] = {k:v for k,v in snapshot.items() if k != 'tail'}
                        record['parent_stderr_capture']['source'] = 'client bounded drain snapshot after owned close'
                        record['parent_stderr_base64'] = base64.b64encode(snapshot['tail']).decode()
                        # This inert parent emits zero diagnostics; authenticate complete empty capture.
                        self.assertTrue(snapshot['complete'])
                        self.assertIsNone(snapshot['error'])
                        self.assertEqual(snapshot['bytes_received'], 0)
                        self.assertEqual(snapshot['tail'], b'')
                    else:
                        record['parent_stderr_base64'] = base64.b64encode(parent.stderr.read().encode()).decode()
                    for name in ('stdin', 'stdout', 'stderr'):
                        getattr(parent, name).close()
                    record['parent_driver_closed_handles'] = [getattr(parent, p).closed for p in ('stdin', 'stdout', 'stderr')]
                else:
                    reader_stream.close()
                if writer is not None:
                    writer.stdin.close()
                    writer.stderr.close()
                    record['writer_driver_closed_handles'] = [writer.stdin.closed, writer.stderr.closed]
                self.save(record)
            self.assertEqual(record['parent_exit_before_close'], 0)
            self.assertTrue(record['close_done_at_checkpoint'])
            self.assertFalse(record['reader_alive_after_release'])
            self.assertFalse(record['caller_alive_after_release'])
            self.assertTrue(record['actual_client_closed'])
            self.assertEqual(record['reader_errors'], [], 'reader lost a valid frame while recording')
            self.assertEqual(record['second_close'], {'return_value': None})
            self.assertTrue(all(record['parent_driver_closed_handles']))
            self.assertNotIn('driver_writer_kill_required', record)
            self.assertNotIn('driver_parent_kill_required', record)
            if held:
                self.assertIsNone(record['writer_exit_before_close'])
                self.assertEqual(record['writer_final_exit'], 0)
                self.assertTrue(all(record['writer_driver_closed_handles']))
                self.assertEqual(record['first_outcome'].get('error_type'), 'TimeoutError')
                self.assertTrue(record['reader_alive_at_checkpoint'])
                self.assertFalse(record['journal_lock_locked_at_checkpoint'])
                self.assertEqual(record['actual_notifications'], [FRAME])
                self.assertEqual(record['actual_responses'], {})
            else:
                self.assertEqual(record['first_outcome'].get('return_value'), None)
                self.assertNotIn('error_type', record['first_outcome'])
                self.assertFalse(record['reader_alive_at_checkpoint'])
                self.assertEqual(record['actual_notifications'], [])
            if journal_enabled:
                self.assertEqual(record['journal_closed_at_checkpoint'], not held)
                self.assertTrue(record['journal_final_closed'])
                rows = [json.loads(line) for line in base64.b64decode(record['journal_final_base64']).decode().splitlines()]
                self.assertEqual(len(rows), int(held))
                if held:
                    self.assertEqual(rows[0]['direction'], 'received')
                    self.assertEqual(rows[0]['message'], FRAME)
                    self.assertEqual(type(rows[0]['observed_ns']), int)
                    self.assertGreater(rows[0]['observed_ns'], 0)

    def test_healthy_eof_retires_reader_and_journal(self):
        self.pipe_case(held=False, journal_enabled=True)

    def test_live_reader_preserves_journal_and_late_frame(self):
        self.pipe_case(held=True, journal_enabled=True)

    def test_live_reader_without_journal_reports_incomplete_and_keeps_frame(self):
        self.pipe_case(held=True, journal_enabled=False)


if __name__ == '__main__':
    unittest.main()
