import sys
import tempfile
import time
import importlib.util
import unittest
from pathlib import Path
from types import SimpleNamespace

from PIL import Image, ImageChops


HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[3]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(REPO_ROOT))

from adapter import CompiledExecution, read_crop_token
AUDIT_PATH = HERE / "audit_saved_frames.py"
AUDIT_SPEC = importlib.util.spec_from_file_location("layout_b_saved_frame_audit", AUDIT_PATH)
assert AUDIT_SPEC is not None and AUDIT_SPEC.loader is not None
AUDIT_MODULE = importlib.util.module_from_spec(AUDIT_SPEC)
AUDIT_SPEC.loader.exec_module(AUDIT_MODULE)


FIXTURE_ROOT = (
    REPO_ROOT
    / "research/live_control/results/integrated-efficiency-live-orchestration-probe-02"
    / "arms/ephemeral/runtime"
)


class CropOCRTests(unittest.TestCase):
    def test_saved_frame_audit_reconciles_pinned_blank_and_filled_frames(self):
        outputs = {
            "068-crop.png": "",
            "077-crop.png": "t991028-4\n",
            "093-crop.png": "ee\n",
            "100-crop.png": "t991028-5\n",
            "115-crop.png": "ee\n",
            "121-crop.png": "t991028-6\n",
        }

        def runner(args, **_kwargs):
            if args[1] == "--version":
                return SimpleNamespace(
                    returncode=0,
                    stdout="tesseract 5.5.0\n leptonica-1.84.1\n",
                    stderr="",
                )
            return SimpleNamespace(
                returncode=0,
                stdout=outputs[Path(args[1]).name],
                stderr="",
            )

        result = AUDIT_MODULE.audit_saved_frames(runner=runner)
        self.assertEqual(result["status"], "PASS_LAYOUT_B_FIT_ONLY")
        self.assertEqual(result["filled_exact"], 3)
        self.assertEqual(result["filled_total"], 3)
        self.assertEqual(result["blank_token_false_positives"], 0)
        self.assertFalse(result["formal_comparison_credit"])

    def test_layout_b_uses_exact_roi_and_explicit_lanczos(self):
        source = FIXTURE_ROOT / "077.png"
        with tempfile.TemporaryDirectory() as directory:
            crop_path = Path(directory) / "crop.png"

            def runner(args, **kwargs):
                actual = Image.open(args[1])
                expected = Image.open(source).crop((495, 541, 803, 577)).convert("L")
                expected = expected.resize(
                    (1848, 216), resample=Image.Resampling.LANCZOS
                )
                self.assertEqual(actual.size, (1848, 216))
                self.assertIsNone(ImageChops.difference(actual, expected).getbbox())
                return SimpleNamespace(returncode=0, stdout="t991028-4\n", stderr="")

            result = read_crop_token(
                source, "B", "t991028-4", crop_path, runner=runner
            )

        self.assertIs(result["exact"], True)
        self.assertEqual(result["stdout"], "t991028-4\n")

    def test_layout_a_keeps_historical_crop_geometry(self):
        source = FIXTURE_ROOT / "005.png"
        with tempfile.TemporaryDirectory() as directory:
            def runner(args, **_kwargs):
                with Image.open(args[1]) as crop:
                    self.assertEqual(crop.size, (848, 60))
                return SimpleNamespace(returncode=0, stdout="", stderr="")

            result = read_crop_token(
                source, "A", "t991000-1", Path(directory) / "crop.png", runner=runner
            )
        self.assertIs(result["exact"], False)

    def test_blank_frame_ocr_garbage_never_matches_expected_token(self):
        source = FIXTURE_ROOT / "093.png"
        with tempfile.TemporaryDirectory() as directory:
            result = read_crop_token(
                source,
                "B",
                "t991028-5",
                Path(directory) / "crop.png",
                runner=lambda *_args, **_kwargs: SimpleNamespace(
                    returncode=0, stdout="ee\n", stderr=""
                ),
            )
        self.assertIs(result["exact"], False)
        self.assertEqual(result["stdout"].strip(), "ee")

    def test_ocr_timeout_is_unknown_and_fails_closed(self):
        source = FIXTURE_ROOT / "093.png"
        with tempfile.TemporaryDirectory() as directory:
            result = read_crop_token(
                source,
                "B",
                "t991028-5",
                Path(directory) / "crop.png",
                runner=lambda *_args, **_kwargs: (_ for _ in ()).throw(
                    TimeoutError("ocr timeout")
                ),
            )
        self.assertIsNone(result["exact"])
        self.assertEqual(result["status"], "unknown")

    def test_nonzero_ocr_exit_is_unknown(self):
        source = FIXTURE_ROOT / "093.png"
        with tempfile.TemporaryDirectory() as directory:
            result = read_crop_token(
                source,
                "B",
                "t991028-5",
                Path(directory) / "crop.png",
                runner=lambda *_args, **_kwargs: SimpleNamespace(
                    returncode=1, stdout="t991028-5\n", stderr="recognizer error"
                ),
            )
        self.assertIsNone(result["exact"])
        self.assertEqual(result["status"], "unknown")


class FakeClient:
    def __init__(self, images, root):
        self.images = iter(images)
        self.runtime = FIXTURE_ROOT
        self.root = root
        self.programs = []
        self.commands = []
        self.sequence = 0

    def _observation(self):
        name, title = next(self.images)
        self.sequence += 1
        return {
            "sequence": self.sequence,
            "capture_ns": time.perf_counter_ns(),
            "image": str(self.runtime / name),
            "context": title,
        }

    def check(self, _alias, _offset, _request_id):
        return {"eligible": True, "status": "VALID"}, {
            "observations": [self._observation()]
        }

    def submit(self, _name, _steps):
        return {"observations": [self._observation()]}

    def clock(self):
        return {"sequence": self.sequence, "runtime_ns": time.perf_counter_ns()}

    def call(self, payload):
        self.commands.append(payload)
        action = payload["command"]["steps"][0]["target_handle"]
        action_name = "enter" if action.endswith("field") else "submit"
        action_id = f"action-{len(self.commands)}"
        terminal = {
            "event": "terminal",
            "id": action_id,
            "status": "completed",
            "release": {
                "verified": True,
                "keys_down": [],
                "buttons_down": [],
            },
        }
        return {"reply": {"records": [terminal]}}, 1000, 2000


class ComposedLayoutBTests(unittest.TestCase):
    def _run(self, ocr_outputs):
        with tempfile.TemporaryDirectory() as directory:
            client = FakeClient(
                [
                    ("068.png", "READY"),
                    ("077.png", "READY"),
                    ("083.png", "AI INTEGRATED SAVED"),
                ],
                Path(directory),
            )
            output_iter = iter(ocr_outputs)

            def runner(_args, **_kwargs):
                return SimpleNamespace(
                    returncode=0, stdout=next(output_iter), stderr=""
                )

            task = {"task_id": "task-4", "token": "t991028-4", "layout": "B"}
            adapter = CompiledExecution(
                client, task, {"field": "task-4-field", "submit": "task-4-submit"},
                ocr_runner=runner,
            )
            return adapter.run(), client

    def test_exact_layout_b_observation_gates_submit(self):
        result, client = self._run(["", "t991028-4\n", "t991028-4\n"])
        receipt = result["receipt"]
        self.assertEqual(receipt["outcome"], "TASK_SUCCEEDED")
        self.assertEqual(receipt["completed_transitions"], 2)
        self.assertEqual(len(client.commands), 2)
        self.assertEqual(
            [row["action"] for row in receipt["transitions"]], ["enter", "submit"]
        )

    def test_blank_or_garbled_layout_b_observation_yields_before_submit(self):
        result, client = self._run(["", "ee\n"])
        receipt = result["receipt"]
        self.assertEqual(receipt["outcome"], "SAFE_YIELD")
        self.assertEqual(receipt["completed_transitions"], 1)
        self.assertEqual(len(client.commands), 1)
        self.assertEqual(receipt["reason"], "effect_failed")


if __name__ == "__main__":
    unittest.main()
