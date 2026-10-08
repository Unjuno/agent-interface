"""Host construction tests for the #55 receipt-aware task socket child."""

import sys
from pathlib import Path
from types import ModuleType
import unittest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from mindustry_three_arm_interactive_v1 import install_receipt_backend


class ReceiptBackendBindingTests(unittest.TestCase):
    def test_installs_only_a_receipt_backend_derived_from_task_backend(self):
        class TaskBackend:
            pass

        class ReceiptBackend(TaskBackend):
            pass

        base = ModuleType("cause_servo_session_v1")
        base.Backend = TaskBackend
        self.assertIs(install_receipt_backend(base, ReceiptBackend), ReceiptBackend)
        self.assertIs(base.Backend, ReceiptBackend)

    def test_rejects_backend_outside_the_task_runtime_lineage(self):
        class TaskBackend:
            pass

        class UnrelatedBackend:
            pass

        base = ModuleType("cause_servo_session_v1")
        base.Backend = TaskBackend
        with self.assertRaisesRegex(TypeError, "must extend"):
            install_receipt_backend(base, UnrelatedBackend)
        self.assertIs(base.Backend, TaskBackend)

    def test_socket_wrapper_targets_the_additive_receipt_child(self):
        source = (HERE / "mindustry_three_arm_socket_v1.py").read_text(encoding="utf-8")
        self.assertIn('"mindustry_three_arm_interactive_v1.py"', source)
        self.assertIn('"interactive_v27.py"', source)


if __name__ == "__main__":
    unittest.main()
