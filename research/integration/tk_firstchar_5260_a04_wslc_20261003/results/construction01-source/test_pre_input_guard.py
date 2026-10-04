import unittest
import candidate
from ready_guard import pre_input_errors


def ready_fixture():
    return {"ready_ns": 30,
        "readiness": {"scheduled": 1, "focus_callbacks": 1, "finalizations": 1},
        "geometry": {"root_id": 10, "target_id": 11, "root_width": 520,
            "root_height": 250, "target_width": 366, "target_height": 23,
            "root_x": 80, "root_y": 70, "target_x": 16, "target_y": 87,
            "target_root_x": 96, "target_root_y": 157}}


class PreInputTests(unittest.TestCase):
    def test_positive_consistent_geometry(self):
        self.assertEqual(pre_input_errors(ready_fixture()), [])

    def test_bad_geometry_and_witness(self):
        for key, value in (("target_root_x", 0), ("target_width", 1), ("target_id", 0)):
            ready = ready_fixture()
            ready["geometry"][key] = value
            self.assertTrue(pre_input_errors(ready))
        ready = ready_fixture()
        ready["readiness"]["scheduled"] = 2
        self.assertTrue(pre_input_errors(ready))

    def test_candidate_refuses_bad_geometry_before_xlib_import(self):
        ready = ready_fixture()
        ready["geometry"]["target_root_x"] = 0
        with self.assertRaisesRegex(RuntimeError, "pre_input_readiness"):
            candidate.click_and_type(ready, {}, {}, None)


if __name__ == "__main__":
    unittest.main()
