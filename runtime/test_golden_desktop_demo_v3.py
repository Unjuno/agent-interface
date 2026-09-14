import unittest
from unittest.mock import patch

import runtime.golden_desktop_demo_v3 as demo


class GoldenDesktopV3DoctorTests(unittest.TestCase):
    def test_doctor_adds_the_runtime_modules_missing_from_v1(self):
        base = {"schema": "old", "passed": True,
                "checks": [{"name": "base", "passed": True, "detail": "ok"}]}
        fake = type("Module", (), {"__version__": "1.2.3"})()
        with patch.object(demo, "BASE_DOCTOR", return_value=base), \
             patch.object(demo.importlib, "import_module", return_value=fake) as imported:
            result = demo.doctor()
        self.assertTrue(result["passed"])
        self.assertEqual(result["schema"], "agent_interface_golden_doctor_v2")
        self.assertEqual([row["name"] for row in result["checks"][-2:]],
                         ["python:openpyxl", "python:et_xmlfile"])
        self.assertEqual(imported.call_count, 2)

    def test_missing_runtime_module_fails_doctor_before_model_work(self):
        base = {"schema": "old", "passed": True,
                "checks": [{"name": "base", "passed": True, "detail": "ok"}]}
        with patch.object(demo, "BASE_DOCTOR", return_value=base), \
             patch.object(demo.importlib, "import_module",
                          side_effect=ModuleNotFoundError("missing")):
            result = demo.doctor()
        self.assertFalse(result["passed"])
        self.assertTrue(all(not row["passed"] for row in result["checks"][-2:]))


if __name__ == "__main__":
    unittest.main()
