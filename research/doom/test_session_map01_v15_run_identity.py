import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

import session_map01_v15 as candidate


class SessionRunIdentityTests(unittest.TestCase):
    def test_v15_passes_run_id_to_the_selected_backend(self):
        received = []
        base = types.ModuleType("session_map01_v12")
        base.vd = types.SimpleNamespace(DoomGame=object)
        base.sys = sys

        def run_base():
            backend = base.Backend(types.SimpleNamespace(name="display"), None,
                                   lambda _row: None, {})
            received.append(backend.run_id)

        base.main = run_base
        executor = types.ModuleType("executor_v13")
        executor.Executor = object
        backend_module = types.ModuleType("doom_owner_thread_release_batch_backend_v1")

        class Backend:
            def __init__(self, _session, _out, _emit, _readers, *, run_id=None):
                self.run_id = run_id
                self.owner = types.SimpleNamespace(close=lambda: None)

        backend_module.Backend = Backend

        class Polling:
            def __init__(self, *_args, **_kwargs):
                pass

            def stats(self):
                return {}

        class Sink:
            def __init__(self, _out):
                pass

            def finalize(self, _stats):
                pass

        saved = {
            name: sys.modules.get(name)
            for name in ("session_map01_v12", "executor_v13",
                         "doom_owner_thread_release_batch_backend_v1")
        }
        try:
            sys.modules.update({
                "session_map01_v12": base,
                "executor_v13": executor,
                "doom_owner_thread_release_batch_backend_v1": backend_module,
            })
            with tempfile.TemporaryDirectory() as tmp, \
                    patch.object(candidate, "_option", side_effect=lambda name, default=None:
                                  tmp if name == "--out" else default), \
                    patch.object(candidate, "MainThreadScorerStdin", Polling), \
                    patch.object(candidate, "ScorerFileSink", Sink), \
                    patch.object(candidate, "_merge_sources", return_value=False):
                candidate.main(run_id="scorer-run-7")
            self.assertEqual(received, ["scorer-run-7"])
        finally:
            for name, original in saved.items():
                if original is None:
                    sys.modules.pop(name, None)
                else:
                    sys.modules[name] = original


if __name__ == "__main__":
    unittest.main()
