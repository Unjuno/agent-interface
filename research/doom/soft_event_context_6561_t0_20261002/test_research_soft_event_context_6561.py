import copy
import unittest

import research_soft_event_context_6561 as target


class SoftEventContextConstructionTests(unittest.TestCase):
    def setUp(self):
        self.binding, self.rows, _ = target.fixture()

    def derive(self, row):
        _, state, count, event, now, _, _raw = row
        return target.candidate_context(state, count, event, now, self.binding)

    def audit(self, row):
        _, state, count, event, now, _, _raw = row
        return target.auditor_derive(state, count, event, now, self.binding)

    def test_frozen_rows_match_oracle_and_independent_auditor(self):
        for row in self.rows:
            with self.subTest(row=row[0]):
                actual = self.derive(row)
                self.assertEqual(actual, row[5])
                self.assertEqual(self.audit(row), actual)
                self.assertTrue(target.auditor_verify_context(
                    row[1], row[6], row[4], self.binding, actual))

    def test_none_is_not_unknown(self):
        none = self.derive(self.rows[0])
        unknown = self.derive(self.rows[4])
        self.assertEqual(none["state"], "NONE")
        self.assertEqual(unknown["state"], "UNKNOWN")
        self.assertNotEqual(none, unknown)

    def test_context_is_prompt_serializable_and_authority_free(self):
        for row in self.rows[1:3]:
            context = self.derive(row)
            prompt = target.render_prompt_context(context)
            self.assertIn('"state":"OBSERVED"', prompt)
            self.assertIn('"grants_input_authority":false', prompt)
            self.assertIn('"task_success_verified":false', prompt)

    def test_future_or_current_event_is_unknown(self):
        row = self.rows[1]
        event = copy.deepcopy(row[3])
        for seq in (row[4], row[4] + 1):
            event["sequence"] = seq
            got = target.candidate_context("observed", 1, event, row[4], self.binding)
            audited = target.auditor_derive("observed", 1, event, row[4], self.binding)
            self.assertEqual(got["state"], "UNKNOWN")
            self.assertEqual(got, audited)

    def test_cross_binding_fails_closed(self):
        row = self.rows[1]
        event = copy.deepcopy(row[3])
        event["signal"]["binding"] = {"session": "other"}
        got = target.candidate_context("observed", 1, event, row[4], self.binding)
        self.assertEqual(got["state"], "UNKNOWN")
        self.assertEqual(got, target.auditor_derive("observed", 1, event, row[4], self.binding))

    def test_authority_mutation_is_detected_by_frozen_contract(self):
        context = self.derive(self.rows[1])
        context["grants_input_authority"] = True
        with self.assertRaises(ValueError):
            target.auditor_verify_context("observed", self.rows[1][6],
                                          self.rows[1][4], self.binding, context)

    def test_old_event_substitution_is_detected_from_raw_history(self):
        row = self.rows[2]
        older = copy.deepcopy(row[6][0])
        emitted_old = target.auditor_derive("observed", 3, older, row[4], self.binding)
        with self.assertRaises(ValueError):
            target.auditor_verify_context("observed", row[6], row[4],
                                          self.binding, emitted_old)

    def test_none_cannot_hide_nonempty_monitor_history(self):
        with self.assertRaises(ValueError):
            target.candidate_context("none", 1, self.rows[1][3], 90, self.binding)


if __name__ == "__main__":
    unittest.main(verbosity=2)

