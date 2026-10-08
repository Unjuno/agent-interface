"""Native receipt references must address exactly the declared JSON location."""
import copy
import unittest

from runtime.cli_v1.receipt_references import (
    NATIVE_REFS, NATIVE_MULTI_REFS, compact_native_receipt, expand_native_receipt,
    compact_receipt, expand_receipt,
)


def projected(path, *, rows=None):
    observation = {"sequence": 7, "native": {"payload": "x" * 2000}}
    marker = {"observation_ref": "/native_result/observation"}
    return {"schema": NATIVE_REFS, "reference_scope": "test",
            "observation_references": [path],
            "native_result": {"observation": observation,
                              "rows": [marker] if rows is None else rows}}


class NativeReferencePointerTests(unittest.TestCase):
    def test_noncanonical_array_indices_are_rejected_without_mutation(self):
        for token in ("-1", "00", "+0", " 0", "0 ", "٠", "０", "-0"):
            with self.subTest(token=token):
                value = projected("/native_result/rows/" + token)
                before = copy.deepcopy(value)
                with self.assertRaises(ValueError):
                    expand_native_receipt(value)
                self.assertEqual(value, before)

    def test_missing_or_scalar_paths_raise_value_error(self):
        for path, rows in (("/native_result/rows/1", None),
                           ("/native_result/missing/0", None),
                           ("/native_result/rows/0/field", [None]),
                           ("/native_result/rows/0/field", [3])):
            with self.subTest(path=path, rows=rows):
                with self.assertRaises(ValueError):
                    expand_native_receipt(projected(path, rows=rows))

    def test_invalid_escape_does_not_select_a_literal_key(self):
        value = projected("/native_result/rows/a~2b", rows={
            "a~2b": {"observation_ref": "/native_result/observation"}})
        with self.assertRaises(ValueError):
            expand_native_receipt(value)

    def test_canonical_array_and_escaped_dictionary_paths_are_lossless(self):
        marker = {"observation_ref": "/native_result/observation"}
        for token, rows, key in (("0", [marker], 0),
                                 ("a~1b~0c", {"a/b~c": marker}, "a/b~c"),
                                 ("-1", {"-1": marker}, "-1"),
                                 ("00", {"00": marker}, "00")):
            with self.subTest(token=token, rows=rows):
                value = projected("/native_result/rows/" + token, rows=rows)
                before = copy.deepcopy(value)
                result = expand_native_receipt(value)
                expected = copy.deepcopy(value)
                for field in ("schema", "reference_scope", "observation_references"):
                    expected.pop(field)
                expected["native_result"]["rows"][key] = expected["native_result"]["observation"]
                self.assertEqual(result, expected)
                self.assertEqual(value, before)

    def test_v2_rejects_the_same_malformed_paths(self):
        for token in ("-1", "00", "+0", " 0", "٠", "1"):
            value = projected("/native_result/rows/" + token)
            path = value["observation_references"][0]
            value["schema"] = NATIVE_MULTI_REFS
            value["observation_references"] = {path: "/native_result/observation"}
            with self.subTest(token=token), self.assertRaises(ValueError):
                expand_native_receipt(value)

    def test_compactor_output_round_trips_and_literal_markers_remain(self):
        observation = {"sequence": 7, "native": {"payload": "x" * 2000}}
        value = {"native_result": {"observation": observation,
                                  "rows": [copy.deepcopy(observation)] * 3,
                                  "literal": {"observation_ref": "unchanged"}}}
        before = copy.deepcopy(value)
        self.assertEqual(expand_native_receipt(compact_native_receipt(value)), value)
        self.assertEqual(value, before)


class EventReferencePointerTests(unittest.TestCase):
    def view(self, token, rows=None):
        return {"schema": "agent-interface/receipt-view-v2-event-refs",
                "event_references": {"/report/rows/" + token: 0},
                "reference_scope": "test", "authority": "none",
                "events": [{"event": "critical", "detail": "exact"}],
                "report": {"rows": [{"event_ref": 0}] if rows is None else rows}}

    def test_noncanonical_array_indices_are_rejected(self):
        for token in ("-1", "00", "+0", " 0", "0 ", "٠", "０", "-0"):
            with self.subTest(token=token), self.assertRaises(ValueError):
                expand_receipt(self.view(token))

    def test_missing_scalar_and_invalid_escape_paths_are_rejected(self):
        for token, rows in (("1", None), ("0/field", [None]),
                            ("a~2b", {"a~2b": {"event_ref": 0}})):
            with self.subTest(token=token), self.assertRaises(ValueError):
                expand_receipt(self.view(token, rows))

    def test_canonical_and_escaped_locations_preserve_input(self):
        for token, rows, key in (("0", [{"event_ref": 0}], 0),
                                 ("a~1b~0c", {"a/b~c": {"event_ref": 0}}, "a/b~c"),
                                 ("-1", {"-1": {"event_ref": 0}}, "-1")):
            value = self.view(token, rows)
            before = copy.deepcopy(value)
            expected = copy.deepcopy(value)
            expected["schema"] = "agent-interface/receipt-view-v1"
            expected.pop("event_references")
            expected.pop("reference_scope")
            expected["report"]["rows"][key] = expected["events"][0]
            with self.subTest(token=token):
                self.assertEqual(expand_receipt(value), expected)
                self.assertEqual(value, before)

    def test_report_root_reference_and_actual_compactor_round_trip(self):
        event = {"event": "terminal", "detail": "exact" * 400}
        value = {"schema": "agent-interface/receipt-view-v1", "events": [event],
                 "report": copy.deepcopy(event), "authority": "none"}
        self.assertEqual(expand_receipt(compact_receipt(value)), value)


if __name__ == "__main__":
    unittest.main()
