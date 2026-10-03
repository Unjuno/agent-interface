import io
import json
import os
from pathlib import Path
import threading
import types
import unittest
from unittest.mock import patch

import codex_app_server_client_v2 as source

class InertProcess:
    def __init__(self, stdout=None):
        self.stdin = io.StringIO()
        self.stdout = stdout if stdout is not None else io.StringIO()
        self.stderr = io.StringIO()
        self.returncode = None
        self.events = []
    def poll(self):
        return self.returncode
    def terminate(self):
        self.events.append("terminate")
    def wait(self, timeout):
        self.returncode = 0
        return 0

class ReaderAccessGateRegression(unittest.TestCase):
    def run_cell(self, mode):
        entered = threading.Event()
        release = threading.Event()
        read_entered = threading.Event()
        release_read = threading.Event()
        rows = []
        faults = []
        readers = []
        journal = io.StringIO()
        process = InertProcess()
        primary = KeyboardInterrupt("controlled acknowledgement interruption")
        real_start = threading.Thread.start
        original_read = source.CodexAppServerClient._read
        parent_ident = threading.get_ident()

        def read(client):
            rows.append({"event": "read", "closed": process.stdout.closed})
            if mode == "running":
                read_entered.set()
                if not release_read.wait(5):
                    raise AssertionError("driver failed to release reader")
            try:
                return original_read(client)
            except BaseException as error:
                faults.append(type(error).__name__)
                return

        def factory(**kwargs):
            t = threading.Thread(**kwargs)
            readers.append(t)
            if mode == "pending":
                original_bootstrap = t._bootstrap_inner
                def gated_bootstrap():
                    entered.set()
                    if not release.wait(5):
                        raise AssertionError("driver failed to release bootstrap")
                    original_bootstrap()
                t._bootstrap_inner = gated_bootstrap
                original_wait = t._started.wait
                def interrupted_ack(timeout=None):
                    if threading.get_ident() == parent_ident:
                        if not entered.wait(2):
                            raise AssertionError("bootstrap not admitted")
                        raise primary
                    return original_wait(timeout)
                t._started.wait = interrupted_ack
                t._test_original_wait = original_wait
            elif mode == "running":
                def start_then_interrupt():
                    real_start(t)
                    if not read_entered.wait(2):
                        raise AssertionError("reader did not enter")
                    raise primary
                t.start = start_then_interrupt
            elif mode == "refused":
                def refused():
                    raise primary
                t.start = refused
            return t

        local = types.SimpleNamespace(Lock=threading.Lock, Condition=threading.Condition, Thread=factory)
        try:
            with patch.object(source, "threading", local), patch.object(source, "open", lambda *a, **k: journal, create=True), patch.object(source.CodexAppServerClient, "_read", read):
                with self.assertRaises(KeyboardInterrupt) as caught:
                    source.CodexAppServerClient(["inert"], process_factory=lambda *a, **k: process, journal_path="inert")
                self.assertIs(caught.exception, primary)
                t = readers[0]
                if mode == "pending":
                    t._started.wait = t._test_original_wait
                if mode == "pending":
                    self.assertIs(threading.Thread.start, real_start)
                    self.assertIs(type(t), threading.Thread)
                    self.assertTrue(entered.is_set())
                    self.assertIsNone(t.ident)
                    self.assertFalse(t._started.is_set())
                    self.assertFalse(release.is_set())
                expected_closed = mode != "running"
                for stream in (process.stdin, process.stdout, process.stderr, journal):
                    self.assertIs(stream.closed, expected_closed)
                self.assertEqual(process.events, ["terminate"])
                self.assertEqual(process.returncode, 0)
                if mode == "running":
                    self.assertTrue(primary.__notes__)
                if mode == "pending":
                    release.set()
                    self.assertTrue(t._started.wait(2))
                    t.join(2)
                    self.assertFalse(t.is_alive())
                    self.assertEqual(rows, [], "cancelled pending reader accessed source")
                    self.assertEqual(faults, [])
                elif mode == "running":
                    release_read.set()
                    t.join(2)
                    self.assertFalse(t.is_alive())
                    self.assertEqual(rows, [{"event": "read", "closed": False}])
                    self.assertEqual(faults, [])
                metric = {"mode": mode, "same_primary": True, "source_closed": expected_closed,
                          "pending_admitted_before_ident": mode == "pending", "read_events": rows,
                          "reader_faults": faults, "owned_started_readers_terminal": mode != "refused"}
                phase = os.environ.get("READER_GATE_PHASE")
                if phase:
                    (Path(__file__).parent / (phase + "-" + mode + ".json")).write_text(json.dumps(metric, indent=2)+"\n", encoding="utf-8")
        finally:
            release.set()
            release_read.set()
            for t in readers:
                if hasattr(t, "_test_original_wait"):
                    t._started.wait = t._test_original_wait
                if mode != "refused" and t._started.wait(2) and t.ident is not None:
                    t.join(2)
                    if t.is_alive():
                        raise AssertionError("owned reader not terminal")
            for stream in (process.stdin, process.stdout, process.stderr, journal):
                stream.close()

    def test_standard_pending_bootstrap_cancellation_prevents_all_later_reads(self):
        self.run_cell("pending")
    def test_running_reader_timeout_preserves_resources_until_driver_retirement(self):
        self.run_cell("running")
    def test_precreation_refusal_cancels_no_reader_and_closes_resources(self):
        self.run_cell("refused")
    def test_healthy_standard_reader_and_adopted_close(self):
        process = InertProcess(io.StringIO('{"id":7,"result":{"ok":true}}\n'))
        journal = io.StringIO()
        with patch.object(source, "open", lambda *a, **k: journal, create=True):
            client = source.CodexAppServerClient(["inert"], process_factory=lambda *a, **k: process, journal_path="inert")
        try:
            client._reader.join(2)
            self.assertFalse(client._reader.is_alive())
            self.assertEqual(client._responses[7]["result"], {"ok": True})
            self.assertEqual(json.loads(journal.getvalue())["message"]["id"], 7)
            client.close()
            self.assertTrue(journal.closed)
        finally:
            client._reader.join(2)
            for stream in (process.stdin, process.stdout, process.stderr, journal):
                stream.close()

if __name__ == "__main__":
    unittest.main()
