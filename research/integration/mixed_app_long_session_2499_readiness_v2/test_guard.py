import unittest

from guard import admit_identity, require_ready


def row(window_id="100", role="calc", generation=1):
    return {"window_id": window_id, "role": role,
            "surface_generation": generation}


def admit(receipt, window="100", generation=1, role="calc"):
    return require_ready(receipt, "geometry", current_window_id=window,
                         current_surface_generation=generation,
                         current_role=role)


class ReadinessGuardTests(unittest.TestCase):
    def test_missing_and_auxiliary_only_refuse_before_operation(self):
        for candidates, expected in [([], "STOP_IDENTITY_MISSING"),
                                     ([row("101", "tip")], "STOP_IDENTITY_AMBIGUOUS")]:
            receipt = admit_identity(candidates, role="calc")
            self.assertEqual(receipt["disposition"], expected)
            self.assertEqual(admit(receipt)["disposition"], "REFUSED_BEFORE_OPERATION")

    def test_malformed_matching_id_and_generation_fail_closed(self):
        for bad in (True, -1, "not-a-window", "0", "01", None):
            receipt = admit_identity([row(bad)], role="calc")
            self.assertEqual(receipt["disposition"], "STOP_IDENTITY_MALFORMED")
        for bad_generation in (True, -1, 1.0, "1", None):
            receipt = admit_identity([row(generation=bad_generation)], role="calc")
            self.assertEqual(receipt["disposition"], "STOP_IDENTITY_MALFORMED")

    def test_malformed_duplicate_cannot_be_masked_by_valid_candidate(self):
        receipt = admit_identity([row(), row("bad")], role="calc")
        self.assertEqual(receipt["disposition"], "STOP_IDENTITY_MALFORMED")

    def test_multiple_main_refuses(self):
        receipt = admit_identity([row(), row("101")], role="calc")
        self.assertEqual(receipt["disposition"], "STOP_IDENTITY_AMBIGUOUS")

    def test_valid_main_with_auxiliary_admits_current_operation(self):
        receipt = admit_identity([row(), row("101", "tip")], role="calc")
        self.assertEqual(admit(receipt), {"disposition": "ADMITTED",
            "operation": "geometry", "window_id": "100",
            "surface_generation": 1, "role": "calc"})

    def test_old_receipt_refuses_after_xid_reuse_or_generation_change(self):
        receipt = admit_identity([row()], role="calc")
        self.assertEqual(admit(receipt, window="101")["reason"], "IDENTITY_STALE")
        self.assertEqual(admit(receipt, generation=2)["reason"], "IDENTITY_STALE")
        self.assertEqual(admit(receipt, role="inkscape")["reason"], "IDENTITY_STALE")


if __name__ == "__main__":
    unittest.main()
