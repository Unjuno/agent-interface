"""Verify successor transports reach every arm's preflight and task calls."""
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch


LIVE = Path(__file__).parent
sys.path.insert(0, str(LIVE))
SPEC = importlib.util.spec_from_file_location(
    "integrated_efficiency_runner_under_test",
    LIVE / "run_integrated_efficiency_live_v1.py")
RUNNER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RUNNER)


class RunnerInjectionTests(unittest.TestCase):
    def test_main_routes_preflights_and_all_arms_through_injected_backends(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            output = root / "output"
            source = root / "source.py"
            source.write_text("candidate allocation source\n", encoding="utf-8")
            digest = hashlib.sha256(source.read_bytes()).hexdigest()
            (output).mkdir()
            (output / "preregistration.json").write_text(json.dumps({
                "schema": "integrated_efficiency_preregistration_v1",
                "status": "frozen_before_preflight_model_calls_and_gui_sessions",
                "study": "injection-contract-test", "seed": 7341,
                "arm_order": list(RUNNER.ARMS),
                "task_schedule": [
                    {"task_id": "task-1", "layout": "A", "phase": "cold"},
                    {"task_id": "task-2", "layout": "A", "phase": "warm"},
                    {"task_id": "task-3", "layout": "A", "phase": "warm"},
                    {"task_id": "task-4", "layout": "B", "phase": "invalidation_repair"},
                    {"task_id": "task-5", "layout": "B", "phase": "post_repair_warm"},
                    {"task_id": "task-6", "layout": "B", "phase": "post_repair_warm"}],
                "sources": {"source.py": digest},
                "scope": "offline injection contract test",
            }), encoding="utf-8")
            (root / "integrated_efficiency_discoveries_v1.json").write_text(
                "{}", encoding="utf-8")

            preflight_calls = []
            task_backends = []
            model_backend = object()

            def preflight(arm, contract):
                preflight_calls.append((arm, contract))
                return {"call_id": "fresh-" + arm, "stage": "schema_preflight",
                        "requested_model": "gpt-5.6-luna",
                        "requested_effort": "low",
                        "usage": {"input_tokens": 1, "output_tokens": 1},
                        "model_visible_images": 0}

            def run_arm(arm, seed, workspace, model_call=None, output_root=None):
                self.assertEqual(seed, 7341)
                self.assertIs(model_call, model_backend)
                self.assertEqual(Path(output_root).resolve(), output.resolve())
                task_backends.append((arm, model_call))
                return [], {"success": True}

            evaluation = {"disposition": "RETAIN",
                          "observed_break_even_task": None,
                          "arms": {arm: {"correct": [],
                                         "cumulative_input_tokens": [0]}
                                   for arm in RUNNER.ARMS}}

            def dump(path, value):
                path = Path(path)
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(json.dumps(value), encoding="utf-8")

            with patch.multiple(RUNNER, HERE=root, OUT=output,
                                run_arm=run_arm, evaluate=lambda _trace: evaluation,
                                dump=dump):
                with redirect_stdout(io.StringIO()):
                    RUNNER.main(model_call=model_backend,
                                schema_preflight=preflight,
                                output_root=output)

            self.assertEqual(preflight_calls, [
                ("plain", "plain"), ("ephemeral", "compiled"),
                ("persistent", "compiled")])
            self.assertEqual([arm for arm, _ in task_backends], list(RUNNER.ARMS))
            trace = json.loads((output / "trace.json").read_text(encoding="utf-8"))
            self.assertEqual(tuple(trace["preflight_calls"]), RUNNER.ARMS)

    def test_main_protects_historical_output_even_when_explicitly_requested(self):
        with self.assertRaisesRegex(RuntimeError, "STOP_HISTORICAL_OUTPUT_ROOT_PROTECTED"):
            RUNNER.main(output_root=RUNNER.LEGACY_OUT)

    def test_main_refuses_nonfresh_successor_output_before_preflight(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "preregistration.json").write_text("{}", encoding="utf-8")
            (root / "old-partial.json").write_text("{}", encoding="utf-8")
            preflight_calls = []
            with self.assertRaisesRegex(RuntimeError, "STOP_SUCCESSOR_OUTPUT_ROOT_NOT_FRESH"):
                RUNNER.main(schema_preflight=lambda *args: preflight_calls.append(args),
                            output_root=root)
            self.assertEqual(preflight_calls, [])

    def test_main_refuses_unfrozen_or_legacy_study_before_preflight(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "preregistration.json").write_text(json.dumps({
                "schema": "integrated_efficiency_preregistration_v1",
                "status": "draft", "study": "integrated-efficiency-live-01",
                "seed": 1, "arm_order": list(RUNNER.ARMS),
                "task_schedule": [], "sources": {"unused.py": "0" * 64},
            }), encoding="utf-8")
            preflight_calls = []
            with self.assertRaisesRegex(
                    RuntimeError, "STOP_SUCCESSOR_PREREGISTRATION_NOT_FROZEN_OR_COMPATIBLE"):
                RUNNER.main(schema_preflight=lambda *args: preflight_calls.append(args),
                            output_root=root)
            self.assertEqual(preflight_calls, [])


if __name__ == "__main__":
    unittest.main()
