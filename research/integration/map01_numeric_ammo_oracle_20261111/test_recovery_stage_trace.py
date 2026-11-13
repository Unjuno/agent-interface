from __future__ import annotations
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from recovery_stage_trace import StageTrace, TracedLock, install


class StageTraceTests(unittest.TestCase):
    def test_send_trace_preserves_return_exception_and_deadline(self):
        from runtime.guarded_win32_v1.process_cancellation import OperationCancellationSupervisor as Supervisor
        calls=[]
        result=object()
        failure=TimeoutError('unchanged cutoff')
        request={'operation_id':'1'*32,'target_generation':'a'*64,'request_id':'2'*32}
        connection=object()
        def send(owner, conn, req, cutoff):
            calls.append((conn,req,cutoff))
            if cutoff==0: raise failure
            return result
        with tempfile.TemporaryDirectory() as td, patch.object(Supervisor,'_send_helper_request',send):
            trace=install(td)
            try:
                owner=object.__new__(Supervisor)
                with trace.scope({'role':'recovery_exchange'}):
                    self.assertIs(owner._send_helper_request(connection,request,123),result)
                    with self.assertRaises(TimeoutError) as caught:
                        owner._send_helper_request(connection,request,0)
                    self.assertIs(caught.exception,failure)
                self.assertIs(owner._send_helper_request(connection,request,456),result)
                self.assertEqual(calls,[(connection,request,123),(connection,request,0),(connection,request,456)])
                self.assertEqual(list(Path(td).iterdir()),[])
                spans=json.loads(trace.flush().read_text())['spans']
                self.assertEqual([s['stage'] for s in spans],['recovery.send']*2)
                self.assertEqual(spans[1]['error_type'],'TimeoutError')
                self.assertTrue(all(s['operation_id']==request['operation_id'] for s in spans))
            finally:
                trace.uninstall()

    def test_helper_lock_trace_preserves_acquire_release(self):
        with tempfile.TemporaryDirectory() as td:
            trace = StageTrace(td)
            lock = TracedLock(threading.Lock(), trace)
            with trace.scope({"role": "recovery_exchange", "operation_id": "1" * 32}):
                self.assertTrue(lock.acquire(timeout=0.1))
                lock.release()
            spans = json.loads(trace.flush().read_text())["spans"]
            self.assertEqual([row["stage"] for row in spans],
                             ["helper.lock.acquire", "helper.lock.release"])
            self.assertTrue(spans[0]["scalar_result"])
            self.assertNotIn("scalar_result", spans[1])

    def test_pipe_poll_and_recv_trace_preserve_message(self):
        from multiprocessing import Pipe
        from multiprocessing.connection import Connection
        with tempfile.TemporaryDirectory() as td:
            trace = install(td)
            parent, child = Pipe(duplex=True)
            try:
                child.send({"request_id": "2" * 32})
                with trace.scope({"role": "recovery_exchange", "operation_id": "1" * 32}):
                    self.assertTrue(parent.poll(0.1))
                    self.assertEqual(parent.recv(), {"request_id": "2" * 32})
                spans = json.loads(trace.flush().read_text())["spans"]
                self.assertEqual([row["stage"] for row in spans],
                                 ["helper.pipe_poll", "helper.pipe_recv"])
                self.assertEqual(spans[1]["request_id"], "2" * 32)
            finally:
                parent.close()
                child.close()
                trace.uninstall()

    def test_wrapper_preserves_arguments_return_identity_and_has_no_early_file_write(self):
        with tempfile.TemporaryDirectory() as td:
            trace = StageTrace(td, clock_ns=iter((10, 20)).__next__)
            value = object()
            calls = []
            def operation(*args, **kwargs):
                calls.append((args, kwargs))
                return value
            self.assertIs(trace.invoke("operation", operation, (value,), {"flag": True}), value)
            self.assertEqual(calls, [((value,), {"flag": True})])
            self.assertEqual(list(Path(td).iterdir()), [])
            data = json.loads(trace.flush().read_text())
            self.assertEqual(data["spans"][0]["start_ns"], 10)
            self.assertEqual(data["spans"][0]["end_ns"], 20)
            self.assertEqual(data["spans"][0]["outcome"], "returned")

    def test_original_exception_survives_and_is_recorded(self):
        with tempfile.TemporaryDirectory() as td:
            trace = StageTrace(td)
            failure = RuntimeError("original")
            def operation():
                raise failure
            with self.assertRaises(RuntimeError) as caught:
                trace.invoke("failure", operation, (), {})
            self.assertIs(caught.exception, failure)
            data = json.loads(trace.flush().read_text())
            self.assertEqual(data["spans"][0]["error_type"], "RuntimeError")

    def test_bounded_buffer_reports_drops_without_skipping_operations(self):
        with tempfile.TemporaryDirectory() as td:
            trace = StageTrace(td, limit=2)
            called = []
            for n in range(4):
                trace.invoke("bounded", called.append, (n,), {})
            data = json.loads(trace.flush().read_text())
            self.assertEqual(called, [0, 1, 2, 3])
            self.assertEqual(len(data["spans"]), 2)
            self.assertEqual(data["dropped_spans"], 2)
            self.assertIs(trace.flush(), trace.flush())

    def test_recovery_helper_keeps_receipt_and_exception_semantics_with_inert_backend(self):
        from runtime.cli_v1 import win32_supervisor_helpers as helpers
        from runtime.cli_v1.test_win32_supervisor_helpers import FakeBackend
        request = {"operation_id": "1" * 32, "target_generation": "a" * 64,
                   "recovery_id": "2" * 32, "request_id": "2" * 32,
                   "deadline_ns": 100, "obligations": ["key:fixture:W:scan_code"]}
        baseline = helpers._recover(request, backend_factory=FakeBackend, clock_ns=lambda: 10)
        with tempfile.TemporaryDirectory() as td:
            trace = install(td)
            try:
                actual = helpers._recover(request, backend_factory=FakeBackend, clock_ns=lambda: 10)
                self.assertEqual(actual, baseline)
                self.assertTrue(actual["release_accepted"])
                data = json.loads(trace.flush().read_text())
                spans = [s for s in data["spans"] if s["stage"] == "helper.recover"]
                self.assertEqual(len(spans), 1)
                self.assertEqual(spans[0]["operation_id"], request["operation_id"])
            finally:
                trace.uninstall()

    def test_spawned_helper_installs_hooks_and_flushes_after_shutdown(self):
        with tempfile.TemporaryDirectory() as td:
            env = dict(os.environ, AI_RECOVERY_TRACE_OUTPUT=td)
            repo = Path(__file__).resolve().parents[3]
            proc = subprocess.run([sys.executable, "-m",
                "research.integration.map01_numeric_ammo_oracle_20261111.stage_trace_spawn_probe"],
                cwd=repo, env=env, capture_output=True, text=True, timeout=20)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            receipt = json.loads(proc.stdout)
            self.assertEqual(receipt["child_exit_code"], 0)
            self.assertEqual(receipt["trace_files"], 2)
            self.assertFalse(receipt["backend_opened"])
            self.assertTrue(receipt["child_lifecycle_span_retained"])
            self.assertTrue(receipt["child_pipe_receive_span_retained"])

    def test_sendinput_shim_calls_the_original_once_and_retains_its_return_count(self):
        from runtime.backends.win32_v1.backend import Win32Backend
        calls = []
        def fake_init(backend, targets):
            def send_input(*args):
                calls.append(args)
                return 1
            backend.user32 = SimpleNamespace(SendInput=send_input)
        with tempfile.TemporaryDirectory() as td, patch.object(Win32Backend, "__init__", fake_init):
            trace = install(td)
            try:
                with trace.scope({"role": "recovery", "operation_id": "1" * 32}):
                    backend = Win32Backend({"inert": 1})
                    self.assertEqual(backend.user32.SendInput(1, None, 40), 1)
                self.assertEqual(calls, [(1, None, 40)])
                data = json.loads(trace.flush().read_text())
                span = next(s for s in data["spans"] if s["stage"] == "native.SendInput")
                self.assertEqual(span["scalar_result"], 1)
                self.assertEqual(span["operation_id"], "1" * 32)
            finally:
                trace.uninstall()


if __name__ == "__main__":
    unittest.main()
