from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import MagicMock, Mock, patch

import runtime.golden_desktop_demo_v2 as demo


USAGE = {"input_tokens": 10, "cached_input_tokens": 5,
         "cache_write_input_tokens": 0, "output_tokens": 2,
         "reasoning_output_tokens": 1}


class FakeGrounding:
    def __init__(self, *_args, **_kwargs):
        self.thread_id = "thread-grounding"
        self.calls = 0

    def call(self, *_args, **_kwargs):
        self.calls += 1
        return {"call_id": f"turn-{self.calls}", "usage": USAGE.copy()}

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return None


class GoldenDesktopV2Tests(unittest.TestCase):
    def test_report_requires_two_same_session_grounding_turns(self):
        self.run_case(native=False)

    def test_native_run_passes_executable_and_checks_required_usage(self):
        self.run_case(native=True)

    def run_case(self, *, native):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            # Import the real arm without requiring its Linux input transport on Windows.
            offline_transport = types.SimpleNamespace(RuntimeClient=object)
            with patch.dict(sys.modules, {"integrated_efficiency_client_v1": offline_transport}):
                import run_integrated_efficiency_live_v1 as implementation

            tasks = [{"task_id": f"task-{i}"} for i in range(6)]
            client_type = MagicMock()
            client = client_type.return_value.__enter__.return_value
            client.ready = {"goal": {"tasks": tasks}}
            client.runtime = root / "runtime"
            client.finish.return_value = {"success": True}
            history = [{**task, "exact": True, "received_ns": 2} for task in tasks]
            session = FakeGrounding()

            def preflight(_arm, _contract):
                (root / "out/workspaces/persistent").mkdir(parents=True)
                (root / "out/arms/persistent").mkdir(parents=True)
                return {"call_id": "preflight", "usage": USAGE.copy()}

            def run_task(_client, _arm, task, index, cached, workspace, model_root, *, model_call):
                self.assertEqual(model_call, session.call)
                calls = []
                if index in (0, 3):
                    calls.append(model_call(model_root, "locate", root / "image", "compiled", workspace))
                row = {
                    "task_id": task["task_id"], "typed_outcome": "completed",
                    "releases_verified": True,
                    "repair": ({"required": True, "old_reference_status": "missing",
                                "old_reference_pointer_admissions": 0,
                                "attempted": True, "succeeded": True}
                               if index == 3 else {"required": False}),
                    "route": "repair" if index == 3 else "cold" if index == 0 else "reuse",
                    "model_calls": calls, "model_visible_images": len(calls),
                    "old_target_pointer_admissions": 0,
                    "input_feedback_ns": [100_000_000], "elapsed_ns": 1_000_000_000,
                }
                return row, cached, {"source": {"capture_ns": 1}}

            config = {"chromium": Path("chrome"), "windows_python": Path("python")}
            if native:
                config["windows_codex_exe"] = root / "codex.exe"
            else:
                config.update(windows_node=Path("node"), windows_cli=Path("cli"))
            health = {"passed": True}
            grounding = Mock(return_value=session)
            with patch.object(demo.base, "doctor", return_value=health), \
                 patch.object(demo.base, "configuration", return_value=config), \
                 patch.object(demo.base, "configure_research_modules",
                              return_value=(implementation, client_type)), \
                 patch.object(demo.base, "windows_arg", return_value="CLI"), \
                 patch.object(implementation, "preflight_call", preflight), \
                 patch.object(implementation, "run_task", run_task), \
                 patch.object(implementation, "records", return_value=history), \
                 patch.object(implementation, "OUT", root / "out"), \
                 patch.object(implementation, "RuntimeClient", client_type):
                report = demo.run_live(root / "out", 1, grounding_model_type=grounding)
            options = grounding.call_args.kwargs
            if native:
                self.assertEqual(options["executable"], config["windows_codex_exe"])
                self.assertIs(options["allow_missing_cache_write"], True)
                self.assertNotIn("node", options)
            else:
                self.assertEqual((options["node"], options["cli"]), (Path("node"), "CLI"))
                self.assertNotIn("executable", options)
        self.assertTrue(report["passed"])
        self.assertEqual(report["grounding_thread_id"], "thread-grounding")
        self.assertEqual(report["grounding_turns"], 2)
        self.assertEqual(report["grounding_call_ids"], ["turn-1", "turn-2"])
        self.assertEqual(report["usage"]["input_tokens"], 30)
        self.assertEqual(report["input_feedback_median_ms"], 100.0)


if __name__ == "__main__":
    unittest.main()
