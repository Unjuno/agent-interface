import copy
import unittest

from .audit import verify
from .candidate import TRACES, check


class IocoT0Tests(unittest.TestCase):
    def test_candidate_scenarios_match_preregistered_dispositions(self):
        for name, trace in TRACES.items():
            with self.subTest(name=name):
                self.assertTrue(check(name, trace)["match"])

    def test_counterexample_is_shortest_prefix_of_supplied_trace(self):
        row = check("stale_unauthorized", TRACES["stale_unauthorized"])
        self.assertEqual(row["counterexample"]["prefix_length"], 2)
        self.assertEqual(row["counterexample"]["state_before"], "STALE")
        self.assertEqual([x["input"] for x in row["counterexample"]["input_history"]], ["OBSERVE_STALE", "ADMIT"])

    def test_explicit_unknown_is_not_silence(self):
        self.assertTrue(check("delayed_explicit_unknown", TRACES["delayed_explicit_unknown"])["accepted"])
        self.assertFalse(check("silent_missing_output", TRACES["silent_missing_output"])["accepted"])

    def test_raw_audit_accepts_candidate_record(self):
        rows = [check(name, trace) for name, trace in TRACES.items()]
        self.assertEqual(verify({
            "study": "issue-5518-ioco-t0-v1",
            "scope": "finite synthetic output-inclusion check; not GUI conformance",
            "alphabet_version": "frozen-v1",
            "quiescence_policy": "explicit UNKNOWN is allowed where listed; missing output is forbidden",
            "results": rows,
        }), [])

    def test_raw_audit_rejects_mutations(self):
        baseline = {
            "study": "issue-5518-ioco-t0-v1",
            "scope": "finite synthetic output-inclusion check; not GUI conformance",
            "alphabet_version": "frozen-v1",
            "quiescence_policy": "explicit UNKNOWN is allowed where listed; missing output is forbidden",
            "results": [check(name, trace) for name, trace in TRACES.items()],
        }
        mutations = []
        x = copy.deepcopy(baseline); x["alphabet_version"] = "changed"; mutations.append(x)
        x = copy.deepcopy(baseline); x["results"].pop(); mutations.append(x)
        x = copy.deepcopy(baseline); x["results"][0]["accepted"] = False; mutations.append(x)
        x = copy.deepcopy(baseline); x["results"][1]["counterexample"]["prefix_length"] = 2; mutations.append(x)
        x = copy.deepcopy(baseline); x["results"][4]["accepted"] = False; mutations.append(x)
        x = copy.deepcopy(baseline); x["results"][5]["internal_hidden_transitions"] = []; mutations.append(x)
        for index, mutation in enumerate(mutations):
            with self.subTest(mutation=index):
                self.assertTrue(verify(mutation))


if __name__ == "__main__":
    unittest.main()

