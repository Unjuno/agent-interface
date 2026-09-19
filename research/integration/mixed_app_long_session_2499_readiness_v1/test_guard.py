import unittest

from guard import admit_identity, require_ready


class ReadinessGuardTests(unittest.TestCase):
    def test_missing_refuses_before_geometry(self):
        receipt = admit_identity([], role="calc")
        self.assertEqual(receipt["disposition"], "STOP_IDENTITY_MISSING")
        self.assertEqual(require_ready(receipt, "geometry")["disposition"], "REFUSED_BEFORE_OPERATION")

    def test_auxiliary_only_refuses(self):
        receipt = admit_identity([{"window_id": "2", "role": "tip"}], role="calc")
        self.assertEqual(receipt["disposition"], "STOP_IDENTITY_AMBIGUOUS")
        self.assertEqual(require_ready(receipt, "input")["disposition"], "REFUSED_BEFORE_OPERATION")

    def test_multiple_main_refuses(self):
        receipt = admit_identity([{"window_id": "1", "role": "calc"}, {"window_id": "2", "role": "calc"}], role="calc")
        self.assertEqual(receipt["disposition"], "STOP_IDENTITY_AMBIGUOUS")

    def test_exactly_one_main_admits(self):
        receipt = admit_identity([{"window_id": "1", "role": "calc"}, {"window_id": "2", "role": "tip"}], role="calc")
        self.assertEqual(require_ready(receipt, "geometry"), {"disposition": "ADMITTED", "operation": "geometry", "window_id": "1"})


if __name__ == "__main__":
    unittest.main()
