import sys
import hashlib
import json
import tempfile
import unittest
import threading
from pathlib import Path
from types import ModuleType
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import map01_overlap_controller_v40 as candidate
import session_map01_v14 as session


class V40CompositionTests(unittest.TestCase):
    def test_session_command_selects_additive_v14_runner(self):
        class Args:
            seed = 17
            load_fixture_manifest = Path("fixture.json")
        command = candidate.session_command(Args(), Path("runtime"))
        self.assertEqual(Path(command[1]).name, "session_map01_v14.py")
        self.assertEqual(command[command.index("--out") + 1], "runtime")
        self.assertIn("--load-fixture-manifest", command)

    def test_session_uses_v13_feedback_and_binds_release_sources(self):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)
            prior_sources = {
                "doom/session_map01_v13.py": "v13",
                "doom/doom_retained_input_backend_v3.py": "release-v3",
                "live_control/input_transition_owner_v3.py": "owner-v3",
            }
            (out / "sources.json").write_text(json.dumps(prior_sources),
                                              encoding="utf-8")
            pipeline = ModuleType("session_map01_v13")
            pipeline.main = lambda: None
            with patch.dict(sys.modules, {"session_map01_v13": pipeline}), \
                    patch.object(sys, "argv", ["session", "--out", str(out)]):
                session.main()
            sources = json.loads((out / "sources.json").read_text())
            self.assertEqual(sources["doom/session_map01_v13.py"], "v13")
            self.assertEqual(sources["doom/doom_retained_input_backend_v3.py"],
                             "release-v3")
            self.assertEqual(sources["live_control/input_transition_owner_v3.py"],
                             "owner-v3")
            for source in ("session_map01_v14.py",
                           "map01_overlap_controller_v39.py",
                           "map01_overlap_controller_v40.py"):
                key = f"doom/{source}"
                digest = hashlib.sha256((HERE / source).read_bytes()).hexdigest()
                self.assertEqual(sources[key], digest)

    def test_v14_runs_real_v13_composition_and_preserves_both_manifests(self):
        import io


        class Game:
            def __init__(self):
                self.initialized = False
                self.closed = False
                self.owner = threading.get_ident()

            def init(self):
                self.initialized = True

            def close(self):
                self.closed = True

            def is_episode_finished(self): return False
            def is_player_dead(self): return False
            def get_game_variable(self, variable): return 0
            def get_episode_time(self): return 100
            def get_ticrate(self): return 35
            def is_episode_timeout_reached(self): return False

        class GV:
            KILLCOUNT = "kills"
            DEATHCOUNT = "deaths"

        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory) / "run"
            base = ModuleType("session_map01_v12")
            telemetry = type("TelemetryBackend", (), {})
            game = Game()
            base.vd = type("VD", (), {
                "DoomGame": lambda: game,
                "GameVariable": GV,
            })
            base.Backend = object
            base.sys = sys

            def base_main():
                out.mkdir(parents=True, exist_ok=True)
                (out / "sources.json").write_text("{}", encoding="utf-8")
                instance = base.vd.DoomGame()
                self.assertIs(base.Backend, telemetry)
                instance.init()
                self.assertEqual(list(base.sys.stdin), ["{\"op\":\"finish\"}"])
                instance.close()

            base.main = base_main
            polling_threads = []

            class FakePolling:
                def __init__(self, stream, sample_fn, sink, sample_hz):
                    self.sample_fn = sample_fn
                    self.sink = sink
                    self.owner = threading.get_ident()
                    polling_threads.append(self.owner)

                def __iter__(self):
                    yield '{"op":"finish"}'

                def stats(self): return {"commands": 1, "eof": False}

            old_stdin, old_argv = sys.stdin, sys.argv
            old_base = sys.modules.get("session_map01_v12")
            old_telemetry = sys.modules.get("doom_retained_input_backend_v3")
            sys.modules["session_map01_v12"] = base
            sys.modules["doom_retained_input_backend_v3"] = ModuleType("doom_retained_input_backend_v3")
            sys.modules["doom_retained_input_backend_v3"].Backend = telemetry
            import session_map01_v13 as measured
            sys.stdin = io.StringIO('{"op":"finish"}\n')
            sys.argv = ["session", "--out", str(out)]
            try:
                with patch.object(measured, "MainThreadScorerStdin", FakePolling):
                    session.main()
            finally:
                sys.stdin, sys.argv = old_stdin, old_argv
                if old_base is None: sys.modules.pop("session_map01_v12", None)
                else: sys.modules["session_map01_v12"] = old_base
                if old_telemetry is None: sys.modules.pop("doom_retained_input_backend_v3", None)
                else: sys.modules["doom_retained_input_backend_v3"] = old_telemetry

            self.assertEqual(polling_threads, [threading.get_ident()])
            summary = json.loads((out / "scorer-summary.json").read_text(encoding="utf-8"))
            self.assertEqual(summary["sample_count"], 1)
            sources = json.loads((out / "sources.json").read_text(encoding="utf-8"))
            for relative in (
                "doom/session_map01_v13.py",
                "doom/doom_retained_input_backend_v3.py",
                "live_control/input_transition_owner_v3.py",
                "doom/session_map01_v14.py",
                "doom/map01_overlap_controller_v39.py",
                "doom/map01_overlap_controller_v40.py",
            ):
                source = (HERE / relative.removeprefix("doom/")
                          if relative.startswith("doom/") else HERE.parent / relative)
                key = relative if relative in sources else relative.replace("/", "\\")
                self.assertEqual(sources[key], hashlib.sha256(source.read_bytes()).hexdigest())


if __name__ == "__main__":
    unittest.main()
