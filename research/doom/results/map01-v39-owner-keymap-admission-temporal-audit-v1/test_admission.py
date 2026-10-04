import unittest

from audit_admission import check_occurrences


def fixture():
    occurrences = []
    events = []
    for index, base in enumerate((100, 200), start=1):
        token = f"C02:{index}"
        occurrences.append({
            "intent_token": token,
            "pre_down": {"sample_finished_ns": base + 10},
            "post_down": {"sample_started_ns": base + 40,
                          "sample_finished_ns": base + 50},
            "post_up": {"sample_started_ns": base + 80},
        })
        events.append({"event": "input_admission", "key": "w",
                       "intent_token": token, "admitted_ns": base + 20,
                       "input_ack_ns": base + 30, "valid_until_ns": base + 100})
    return {"occurrences": occurrences, "events": events}


class AdmissionTemporalAuditTests(unittest.TestCase):
    def test_ordered_occurrence_local_admission_passes(self):
        self.assertEqual(check_occurrences(fixture()), (True, []))

    def test_missing_admission_timestamp_fails(self):
        raw = fixture()
        del raw["events"][0]["input_ack_ns"]
        ok, errors = check_occurrences(raw)
        self.assertFalse(ok)
        self.assertTrue(any("integers" in error for error in errors))

    def test_admission_after_down_fails(self):
        raw = fixture()
        raw["events"][0]["admitted_ns"] = 151
        raw["events"][0]["input_ack_ns"] = 152
        ok, errors = check_occurrences(raw)
        self.assertFalse(ok)
        self.assertTrue(any("not bound" in error for error in errors))

    def test_cross_occurrence_admission_fails(self):
        raw = fixture()
        raw["events"][0]["intent_token"] = "C02:2"
        ok, errors = check_occurrences(raw)
        self.assertFalse(ok)
        self.assertTrue(any("expected exactly one" in error for error in errors))

    def test_expired_lease_at_down_fails(self):
        raw = fixture()
        raw["events"][0]["valid_until_ns"] = 149
        ok, errors = check_occurrences(raw)
        self.assertFalse(ok)
        self.assertTrue(any("lease expired" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
