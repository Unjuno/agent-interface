import json
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
for _name in ("map01_scorer_stdio_adapter_v1", "independent_progress_clock_v2"):
    sys.modules.setdefault(_name, types.ModuleType(_name))
sys.modules["map01_scorer_stdio_adapter_v1"].MainThreadScorerStdin = type("Polling", (), {})
sys.modules["map01_scorer_stdio_adapter_v1"].ScorerFileSink = type("Sink", (), {})
sys.modules["independent_progress_clock_v2"].ProgressSample = type("ProgressSample", (), {})
import session_map01_v14 as candidate


class SessionSelectionTests(unittest.TestCase):
    def test_v14_selects_v3_and_hashes_the_owner_receipt_chain(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            (out / "sources.json").write_text("{}", encoding="utf-8")
            scorer = types.ModuleType("map01_scorer_stdio_adapter_v1")
            scorer.MainThreadScorerStdin = type("Polling", (), {
                "__init__": lambda self, *args, **kwargs: None,
                "stats": lambda self: {},
            })
            scorer.ScorerFileSink = type("Sink", (), {
                "__init__": lambda self, *args, **kwargs: None,
                "finalize": lambda self, *args: None,
            })
            clock = types.ModuleType("independent_progress_clock_v2")
            clock.ProgressSample = type("ProgressSample", (), {})
            old_scorer = sys.modules.get("map01_scorer_stdio_adapter_v1")
            old_clock = sys.modules.get("independent_progress_clock_v2")
            sys.modules["map01_scorer_stdio_adapter_v1"] = scorer
            sys.modules["independent_progress_clock_v2"] = clock
            base = types.ModuleType("session_map01_v12")
            base.vd = types.SimpleNamespace(DoomGame=object)
            base.sys = sys
            telemetry = types.ModuleType("doom_owner_thread_release_batch_backend_v1")
            telemetry.Backend = type("SelectedBackend", (), {})
            names = {
                "session_map01_v12": sys.modules.get("session_map01_v12"),
                "doom_owner_thread_release_batch_backend_v1": sys.modules.get("doom_owner_thread_release_batch_backend_v1"),
            }
            sys.modules.update({"session_map01_v12": base,
                                "doom_owner_thread_release_batch_backend_v1": telemetry})
            try:
                with patch.object(candidate, "MainThreadScorerStdin") as polling, \
                     patch.object(candidate, "ScorerFileSink") as sink:
                    with patch.object(base, "main", return_value=None, create=True) as run_base:
                        oldargv, oldstdin = sys.argv, sys.stdin
                        sys.argv = ["session", "--out", str(out)]
                        try:
                            candidate.main()
                        finally:
                            sys.argv, sys.stdin = oldargv, oldstdin
                    self.assertIs(base.Backend, telemetry.Backend)
                    run_base.assert_called_once()
                manifest = json.loads((out / "sources.json").read_text(encoding="utf-8"))
                manifest = {name.replace("\\", "/"): value
                            for name, value in manifest.items()}
                for name in (
                    "doom/doom_owner_thread_release_batch_backend_v1.py",
                    "doom/doom_typed_release_backend_v2.py",
                    "live_control/input_transition_owner_v4.py",
                    "live_control/input_transition_owner_v3.py",
                    "live_control/input_owner_v12.py",
                    "live_control/input_owner_v11.py",
                ):
                    self.assertIn(name, manifest)
                    self.assertEqual(len(manifest[name]), 64)
            finally:
                for name, old in names.items():
                    if old is None:
                        sys.modules.pop(name, None)
                    else:
                        sys.modules[name] = old
                if old_scorer is None:
                    sys.modules.pop("map01_scorer_stdio_adapter_v1", None)
                else:
                    sys.modules["map01_scorer_stdio_adapter_v1"] = old_scorer
                if old_clock is None:
                    sys.modules.pop("independent_progress_clock_v2", None)
                else:
                    sys.modules["independent_progress_clock_v2"] = old_clock


if __name__ == "__main__":
    unittest.main()
