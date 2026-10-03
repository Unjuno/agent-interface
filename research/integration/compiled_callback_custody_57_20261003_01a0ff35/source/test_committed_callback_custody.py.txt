"""Callback-local event processing must not change compiled receipt evidence."""
import unittest

from runtime.core_v1.test_compiled_gui import Driver


class CompiledJournalCustodyTests(unittest.TestCase):
    def test_journal_top_level_and_nested_edits_leave_branch_evidence_intact(self):
        driver = Driver()

        def journal(event):
            driver.record("journal", event)
            if event["event"] == "branch_selected":
                event["action"] = "logger-local"
                event["matched_conditions"]["phase"] = 99

        driver.journal = journal
        receipt = driver.run()
        branches = [event for event in receipt["critical_events"]
                    if event["event"] == "branch_selected"]
        self.assertEqual([(event["action"], event["matched_conditions"])
                          for event in branches],
                         [("enter", {"phase": 0}), ("save", {"phase": 1}),
                          (None, {"phase": 2})])
        self.assertEqual(receipt["outcome"], "TASK_SUCCEEDED")
        self.assertEqual(receipt["completed_transitions"], 2)

    def test_journal_can_clear_its_payload_after_an_executed_action(self):
        driver = Driver()

        def journal(event):
            driver.record("journal", event)
            if event["event"] == "action_terminal":
                event.clear()

        driver.journal = journal
        try:
            receipt = driver.run()
        except KeyError as error:
            self.fail(f"callback-local event clearing interrupted the graph: {error}")
        terminals = [event for event in receipt["critical_events"]
                     if event["event"] == "action_terminal"]
        self.assertEqual([(event["action"], event["status"],
                           event["release_verified"]) for event in terminals],
                         [("enter", "completed", True), ("save", "completed", True)])
        self.assertEqual(receipt["outcome"], "TASK_SUCCEEDED")
        self.assertEqual(receipt["completed_transitions"], 2)

    def test_retained_journal_payloads_cannot_rewrite_the_returned_receipt(self):
        driver = Driver()
        receipt = driver.run()
        for event in driver.calls["journal"]:
            event.clear()
        self.assertEqual([event.get("event") for event in receipt["critical_events"]],
                         ["branch_selected", "action_terminal", "effect_checked",
                          "branch_selected", "action_terminal", "effect_checked",
                          "branch_selected", "runtime_finished"])
        self.assertEqual(receipt["critical_events"][-1]["outcome"], "TASK_SUCCEEDED")
        self.assertEqual(receipt["critical_events"][-1]["completed_transitions"], 2)

    def test_journal_edits_cannot_hide_a_completed_prefix_at_safe_yield(self):
        driver = Driver("observe", 2)

        def journal(event):
            driver.record("journal", event)
            if event["event"] == "action_terminal":
                event.update(action="logger-local", status="refused", release_verified=False)

        driver.journal = journal
        receipt = driver.run()
        terminal = next(event for event in receipt["critical_events"]
                        if event["event"] == "action_terminal")
        self.assertEqual((terminal["action"], terminal["status"],
                          terminal["release_verified"]), ("enter", "completed", True))
        self.assertEqual((receipt["outcome"], receipt["reason"]),
                         ("SAFE_YIELD", "budget_exhausted"))
        self.assertEqual(receipt["completed_transitions"], 1)
        self.assertEqual(receipt["pending_effect"]["action"], "enter")

    def test_journal_exception_still_propagates_before_dispatch(self):
        driver = Driver()

        def journal(event):
            raise RuntimeError("journal unavailable")

        driver.journal = journal
        with self.assertRaisesRegex(RuntimeError, "journal unavailable"):
            driver.run()
        self.assertEqual(driver.calls["admit"], [])
        self.assertEqual(driver.calls["execute"], [])


class CompiledObservationRequestCustodyTests(unittest.TestCase):
    def test_observer_can_consume_its_requested_predicate_list(self):
        driver = Driver()
        observe = driver.observe
        requested = []

        def consuming_observer(request):
            requested.append(request["required_predicates"].copy())
            request["required_predicates"].clear()
            return observe(request)

        driver.observe = consuming_observer
        try:
            receipt = driver.run()
        except ValueError as error:
            self.fail(f"observer payload processing changed private declarations: {error}")
        self.assertEqual(requested, [["phase"], ["phase"], ["phase"]])
        self.assertEqual(receipt["outcome"], "TASK_SUCCEEDED")
        self.assertEqual([entry["action"] for entry in receipt["transitions"]],
                         ["enter", "save"])
        self.assertEqual([entry["predicates"] for entry in receipt["observations"]],
                         [{"phase": 0}, {"phase": 1}, {"phase": 2}])

    def test_retained_observer_request_cannot_change_later_declarations(self):
        driver = Driver()

        def journal(event):
            driver.record("journal", event)
            if event["event"] == "action_terminal" and len(driver.calls["observe"]) == 1:
                driver.calls["observe"][0]["required_predicates"].clear()

        driver.journal = journal
        try:
            receipt = driver.run()
        except ValueError as error:
            self.fail(f"retained request changed subsequent observation admission: {error}")
        self.assertEqual(receipt["outcome"], "TASK_SUCCEEDED")
        self.assertEqual(receipt["completed_transitions"], 2)
        self.assertEqual([entry["action"] for entry in receipt["transitions"]],
                         ["enter", "save"])
        self.assertEqual(driver.calls["observe"][1]["required_predicates"], ["phase"])


if __name__ == "__main__":
    unittest.main()
