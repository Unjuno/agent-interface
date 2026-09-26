import copy
import json
import tempfile
import unittest
from pathlib import Path

from audit_cpu_gate import audit, validate
from render_audit import candidate, specs


class CpuGateTests(unittest.TestCase):
    def test_out_of_bounds_corruption_refuses(self):
        value = candidate(specs()[0]["geometry"])
        value["field"]["point"]["x"] = 1280
        with self.assertRaises(ValueError):
            validate(value)

    def test_duplicate_target_refuses(self):
        value = candidate(specs()[0]["geometry"])
        value["submit"] = copy.deepcopy(value["field"])
        with self.assertRaises(ValueError):
            validate(value)

    def test_wrong_method_refuses(self):
        value = candidate(specs()[0]["geometry"])
        value["method"]["second_action"] = "click_anywhere"
        with self.assertRaises(ValueError):
            validate(value)

    def test_manifest_png_tampering_refuses(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            from render_audit import main
            # Render into a temporary evidence directory via the script entrypoint.
            import os
            old = os.environ.get("RESULT_ROOT")
            os.environ["RESULT_ROOT"] = tmp
            try:
                main()
            finally:
                if old is None:
                    os.environ.pop("RESULT_ROOT", None)
                else:
                    os.environ["RESULT_ROOT"] = old
            self.assertEqual(audit(root)["status"], "PASS_CPU_RENDERER_COORDINATE_GATE")
            path = root / "family-01-v0.png"
            path.write_bytes(path.read_bytes() + b"tamper")
            with self.assertRaises(ValueError):
                audit(root)


if __name__ == "__main__":
    unittest.main()
