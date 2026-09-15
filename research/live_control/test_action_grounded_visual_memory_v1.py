import copy
import json
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from action_grounded_visual_memory_v1 import retrieve, sha256_bytes, validate, verify_artifact


def fixture(root):
    image = Image.new("RGB", (4, 3), (10, 20, 30))
    path = root / "target.png"
    image.save(path)
    digest = sha256_bytes(image.tobytes())
    return {
        "schema": "action-grounded-visual-memory-v1", "memory_id": "m1",
        "task": {"task_id": "task", "environment_id": "env"},
        "source": {"session_id": "session", "sequence": 2, "capture_ns": 10,
                   "exact": True, "surface": 9, "geometry": [0, 0, 10, 10],
                   "frame_size": [10, 10],
                   "image_name": "frame.png", "image_sha256": "1" * 64,
                   "rgb_sha256": "2" * 64},
        "target": {"name": "save", "handle": "h1", "point": [2, 1],
                   "crop_box": [0, 0, 4, 3], "patch_sha256": digest},
        "action": {"id": "a1", "program_sha256": "3" * 64, "accepted_ns": 20,
                   "terminal_ns": 30, "status": "completed", "release_verified": True,
                   "keys_down": [], "buttons_down": []},
        "effect": {"predicate_id": "p1", "sequence": 3, "capture_ns": 25,
                   "success": True, "reason": "matched", "frame_sha256": "4" * 64,
                   "artifact_sha256": "5" * 64, "reconciled_exact": True,
                   "independent_output_sha256": "6" * 64},
        "recovery": {"path": "local", "route": "reuse->local", "trace": [],
                     "model_call_ids": [], "attempted_model_calls": 0,
                     "completed_model_calls": 0, "model_wait_ns": 0},
        "artifact": {"path": "target.png", "width": 4, "height": 3,
                     "png_sha256": sha256_bytes(path.read_bytes()), "rgb_sha256": digest},
        "retention": {"class": "conditional_visual_reference",
                      "requires_current_observation": True,
                      "requires_fresh_input_admission": True},
        "authority": "none"}


class TestMemory(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.receipt = fixture(self.root)

    def tearDown(self): self.temp.cleanup()

    def context(self):
        return {"task_id": "task", "environment_id": "env", "session_id": "session",
                "surface": 9, "target_name": "save", "current_observation_exact": True}

    def test_valid_and_artifact_verified_without_authority(self):
        self.assertEqual(validate(self.receipt), self.receipt)
        result = verify_artifact(self.receipt, self.root)
        self.assertEqual(result["status"], "VERIFIED_ARCHIVED_REFERENCE")
        self.assertEqual(result["current_target_status"], "unknown")
        self.assertEqual(result["authority"], "none")

    def test_matching_retrieval_still_requires_revalidation_and_admission(self):
        result = retrieve(self.receipt, self.context())
        self.assertEqual(result["status"], "ELIGIBLE_VISUAL_REFERENCE")
        self.assertEqual(result["current_target_status"], "must_be_revalidated")
        self.assertEqual(result["input_admission"], "must_be_fresh")
        self.assertEqual(result["authority"], "none")

    def test_context_mismatches_fail_closed(self):
        for field, value in (("task_id", "other"), ("environment_id", "other"),
                             ("session_id", "other"), ("surface", 10),
                             ("target_name", "other"), ("current_observation_exact", False)):
            with self.subTest(field=field):
                context = self.context(); context[field] = value
                result = retrieve(self.receipt, context)
                self.assertEqual(result["status"], "NOT_ELIGIBLE")
                self.assertIsNone(result["reference"])

    def test_modified_artifact_is_rejected(self):
        (self.root / "target.png").write_bytes(b"changed")
        with self.assertRaisesRegex(ValueError, "changed"):
            verify_artifact(self.receipt, self.root)

    def test_artifact_path_escape_is_rejected(self):
        bad = copy.deepcopy(self.receipt); bad["artifact"]["path"] = "../target.png"
        with self.assertRaisesRegex(ValueError, "artifact"):
            validate(bad)

    def test_missing_release_is_rejected(self):
        bad = copy.deepcopy(self.receipt); bad["action"]["release_verified"] = False
        with self.assertRaisesRegex(ValueError, "release"):
            validate(bad)

    def test_effect_before_source_is_rejected(self):
        bad = copy.deepcopy(self.receipt); bad["effect"]["sequence"] = 2
        with self.assertRaisesRegex(ValueError, "effect"):
            validate(bad)

    def test_effect_before_action_acceptance_is_rejected(self):
        bad = copy.deepcopy(self.receipt); bad["effect"]["capture_ns"] = 19
        with self.assertRaisesRegex(ValueError, "action lifetime"):
            validate(bad)

    def test_patch_binding_is_rejected_when_hash_differs(self):
        bad = copy.deepcopy(self.receipt); bad["artifact"]["rgb_sha256"] = "7" * 64
        with self.assertRaisesRegex(ValueError, "bind"):
            validate(bad)

    def test_unknown_field_is_rejected(self):
        bad = copy.deepcopy(self.receipt); bad["extra"] = True
        with self.assertRaisesRegex(ValueError, "fields"):
            validate(bad)


if __name__ == "__main__": unittest.main()
