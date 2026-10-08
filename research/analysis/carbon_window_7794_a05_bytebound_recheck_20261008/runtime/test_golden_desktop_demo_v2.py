from pathlib import Path
import tempfile
import types
import unittest
from unittest.mock import patch

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

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return None


class GoldenDesktopV2Tests(unittest.TestCase):
    def test_report_requires_two_same_session_grounding_turns(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            implementation = types.SimpleNamespace()

            def preflight(_arm, _contract):
                (root / "out/workspaces/persistent").mkdir(parents=True)
                return {"call_id": "preflight", "usage": USAGE.copy()}

            def run_arm(_arm, _seed, _workspace):
                implementation.call_model(None, None, None, None, None)
                implementation.call_model(None, None, None, None, None)
                rows = []
                for index in range(6):
                    rows.append({
                        "exact_submission": True, "releases_verified": True,
                        "repair": ({"required": True, "old_reference_status": "missing",
                                    "old_reference_pointer_admissions": 0,
                                    "attempted": True, "succeeded": True}
                                   if index == 3 else {"required": False}),
                        "route": "repair" if index == 3 else "cold" if index == 0 else "reuse",
                        "model_calls": ([{"call_id": "turn-1", "usage": USAGE.copy()}]
                                        if index == 0 else
                                        [{"call_id": "turn-2", "usage": USAGE.copy()}]
                                        if index == 3 else []),
                        "model_visible_images": 1 if index in (0, 3) else 0,
                        "old_target_pointer_admissions": 0,
                        "input_feedback_ns": [100_000_000],
                        "elapsed_ns": 1_000_000_000,
                    })
                return rows, {"success": True}

            implementation.preflight_call = preflight
            implementation.run_arm = run_arm
            config = {"chromium": Path("chrome"), "windows_node": Path("node"),
                      "windows_cli": Path("cli"), "windows_python": Path("python")}
            health = {"passed": True}
            with patch.object(demo.base, "doctor", return_value=health), \
                 patch.object(demo.base, "configuration", return_value=config), \
                 patch.object(demo.base, "configure_research_modules",
                              return_value=(implementation, object)), \
                 patch.object(demo.base, "windows_arg", return_value="CLI"):
                report = demo.run_live(root / "out", 1, grounding_model_type=FakeGrounding)
        self.assertTrue(report["passed"])
        self.assertEqual(report["grounding_thread_id"], "thread-grounding")
        self.assertEqual(report["grounding_turns"], 2)
        self.assertEqual(report["grounding_call_ids"], ["turn-1", "turn-2"])
        self.assertEqual(report["usage"]["input_tokens"], 30)
        self.assertEqual(report["input_feedback_median_ms"], 100.0)


if __name__ == "__main__":
    unittest.main()
