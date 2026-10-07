"""Startup-failure journal custody regressions; no child process is launched."""
import builtins
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import codex_app_server_client_v2 as client_module


class CloseFailureJournal:
    def __init__(self, stream, error):
        self.stream = stream
        self.error = error
        self.calls = 0

    @property
    def closed(self):
        return self.stream.closed

    def close(self):
        self.calls += 1
        raise self.error


class StartupJournalTests(unittest.TestCase):
    def test_factory_failure_closes_owned_journal_and_preserves_startup_error(self):
        startup_error = OSError("injected process factory failure")
        factory_calls = []

        def fail_factory(command, **kwargs):
            factory_calls.append((command, kwargs))
            raise startup_error

        with tempfile.TemporaryDirectory(prefix="startup-journal-main-") as temporary:
            path = Path(temporary) / "startup.jsonl"
            client = object.__new__(client_module.CodexAppServerClient)
            caught = None
            try:
                client_module.CodexAppServerClient.__init__(
                    client, ["not-launched"], process_factory=fail_factory, journal_path=path
                )
            except BaseException as error:
                caught = error

            self.assertIs(caught, startup_error)
            self.assertEqual(len(factory_calls), 1)
            self.assertTrue(client._journal.closed)
            self.assertEqual(path.read_bytes(), b"")
            self.assertFalse(hasattr(client, "process"))

    def test_close_failure_remains_cause_of_original_startup_error(self):
        startup_error = OSError("injected process factory failure")
        close_error = OSError("injected journal close failure")
        journals = []

        def tracked_open(*args, **kwargs):
            stream = builtins.open(*args, **kwargs)
            journal = CloseFailureJournal(stream, close_error)
            journals.append(journal)
            return journal

        def fail_factory(command, **kwargs):
            raise startup_error

        with tempfile.TemporaryDirectory(prefix="startup-journal-close-failure-") as temporary:
            path = Path(temporary) / "startup.jsonl"
            client = object.__new__(client_module.CodexAppServerClient)
            caught = None
            try:
                with patch.dict(client_module.__dict__, {"open": tracked_open}):
                    client_module.CodexAppServerClient.__init__(
                        client, ["not-launched"], process_factory=fail_factory, journal_path=path
                    )
            except BaseException as error:
                caught = error
            finally:
                if journals:
                    journals[0].stream.close()

            self.assertIs(caught, startup_error)
            self.assertIs(caught.__cause__, close_error)
            self.assertEqual(journals[0].calls, 1)
            self.assertFalse(hasattr(client, "process"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
