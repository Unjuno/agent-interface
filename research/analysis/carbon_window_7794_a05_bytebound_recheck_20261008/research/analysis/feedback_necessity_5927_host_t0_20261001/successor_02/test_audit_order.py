import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
PACKAGE = HERE.parent
sys.path.insert(0, str(PACKAGE))
sys.path.insert(0, str(HERE))

import fixtures
from feedback_necessity import run_candidate
from audit_feedback_necessity_v2 import audit_result


class AuditOrderTests(unittest.TestCase):
    def test_same_partition_set_passes_despite_row_order_difference(self):
        case = fixtures.positive_case()
        candidate = run_candidate([case])
        audited = audit_result([case], candidate)
        self.assertEqual(audited["status"], "PASS_RAW_AUDIT")


if __name__ == "__main__":
    unittest.main()
