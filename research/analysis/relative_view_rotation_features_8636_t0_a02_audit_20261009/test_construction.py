import importlib.util
from pathlib import Path
import unittest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("audit_only", HERE / "audit.py")
audit_only = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit_only)

class AuditConstructionTests(unittest.TestCase):
    def test_image_arms_fail_closed_for_frozen_invalid_observations(self):
        for fault in ("hide_second", "swap_ids", "move_third", "near_singular", "low_texture", "camera_translation", "stale_frame", "viewport_resize"):
            with self.subTest(fault=fault):
                self.assertTrue(audit_only.expected_fault_for_arm(fault, "raw_pixels"))
                self.assertTrue(audit_only.expected_fault_for_arm(fault, "spherical_features"))
        self.assertFalse(audit_only.expected_fault_for_arm("range_variation", "raw_pixels"))

    def test_pose_reference_still_depends_on_shared_landmark_detection(self):
        self.assertTrue(audit_only.expected_fault_for_arm("hide_second", "viewstate_oracle"))
        self.assertTrue(audit_only.expected_fault_for_arm("low_texture", "viewstate_oracle"))
        for fault in ("swap_ids", "move_third", "near_singular", "camera_translation", "stale_frame", "viewport_resize", "range_variation"):
            with self.subTest(fault=fault):
                self.assertFalse(audit_only.expected_fault_for_arm(fault, "viewstate_oracle"))

    def test_release_and_generation_negative_controls(self):
        valid = [{"trial":"t","event_type":"OBSERVATION","step":0}, {"trial":"t","event_type":"RELEASE","step":1,"status":"RELEASE","release_verified":True,"action":[0.0,0.0]}]
        audit_only.check_order(valid)
        audit_only.check_release(valid)
        with self.assertRaises(ValueError):
            audit_only.check_release(valid[:-1])
        with self.assertRaises(ValueError):
            audit_only.check_generation({"target_generation":3,"viewport_generation":4})

if __name__ == "__main__":
    unittest.main()
