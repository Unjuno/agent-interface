import copy
import unittest

import auditor
import candidate
from build_cases import build_cases


class SlackReclamationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.frozen = build_cases()

    def test_seeded_matrix_covers_jobs_bursts_and_positive_slack(self):
        cases = self.frozen["cases"]
        self.assertEqual(len(cases), 18)
        self.assertEqual({len(c["controls"]) for c in cases}, {1, 2, 3})
        self.assertTrue(any(c["positive_slack_subset"] for c in cases))
        self.assertTrue(any(c["case_id"] == "exact-boundary" for c in cases))
        self.assertTrue(any(c["case_id"] == "joint-infeasible" for c in cases))
        self.assertTrue(any(
            len({j["actual_release"] for j in c["controls"]}) < len(c["controls"])
            for c in cases
        ))
        for case in cases:
            self.assertTrue(all(
                max(job["release_choices"]) + job["relative_deadline"] <= case["horizon"]
                for job in case["controls"]
            ))

    def test_refusal_gate_fails_closed_on_class_wcET_and_preemption(self):
        controls = {x["id"]: x for x in self.frozen["refusal_controls"]}
        for key in ("unknown-wcet", "nonpreemptible", "invalid-job-class"):
            control = controls[key]
            self.assertEqual(candidate.refusal_status(control["job"]), control["expected"])
            self.assertEqual(auditor.classify(control["job"]), control["expected"])

    def test_candidate_reservation_charges_dispatch_and_work(self):
        case = next(c for c in self.frozen["cases"] if c["case_id"] == "late_single-01")
        result = candidate.simulate(case, "STATIC_RESERVATION", 1)
        counts = {}
        for event in result["events"]:
            if event["kind"].startswith("control_"):
                counts[event["period"]] = counts.get(event["period"], 0) + 1
            if event["kind"].startswith("soft_"):
                key = (event["period"], "soft")
                counts[key] = counts.get(key, 0) + 1
        self.assertTrue(all(value <= 2 for key, value in counts.items() if isinstance(key, int)))
        self.assertTrue(all(value <= 6 for key, value in counts.items() if isinstance(key, tuple)))

    def test_candidate_records_consistent_one_slot_events(self):
        case = next(c for c in self.frozen["cases"] if c["case_id"] == "boundary_burst_pair-01")
        result = candidate.simulate(case, "DEMAND_GUARDED_SLACK_STEAL", 0)
        self.assertEqual([e["tick"] for e in result["events"]], list(range(case["horizon"])))
        self.assertEqual(result["summary"]["cpu_busy_ticks"], sum(e["kind"] != "idle" for e in result["events"]))

    def test_pre_release_actions_do_not_read_selected_future_release(self):
        case = copy.deepcopy(next(c for c in self.frozen["cases"] if c["case_id"] == "late_single-01"))
        job = case["controls"][0]
        alternatives = [r for r in job["release_choices"] if r != job["actual_release"]]
        self.assertTrue(alternatives)
        earlier = candidate.simulate(case, "DEMAND_GUARDED_SLACK_STEAL", 0)["events"]
        changed = copy.deepcopy(case)
        changed["controls"][0]["actual_release"] = alternatives[0]
        later = candidate.simulate(changed, "DEMAND_GUARDED_SLACK_STEAL", 0)["events"]
        cutoff = min(job["actual_release"], alternatives[0])
        self.assertEqual(earlier[:cutoff], later[:cutoff])

    def test_exhaustive_oracle_includes_exact_and_infeasible_boundaries(self):
        exact = next(c for c in self.frozen["cases"] if c["case_id"] == "exact-boundary")
        infeasible = next(c for c in self.frozen["cases"] if c["case_id"] == "joint-infeasible")
        self.assertTrue(auditor.actual_control_oracle(exact, 0))
        self.assertFalse(auditor.actual_control_oracle(infeasible, 0))
        self.assertEqual(auditor.maximum_soft_work_oracle(exact, 0), 28)

    def test_auditor_rejects_frozen_input_and_raw_event_mutations(self):
        fixture = copy.deepcopy(self.frozen)
        fixture["cases"] = [fixture["cases"][0]]
        rows, refusals = candidate.run(fixture)
        clean = auditor.audit(rows, refusals, fixture)
        self.assertEqual(clean["errors"], [])
        self.assertEqual(clean["method_status"], "PASS_METHOD_SCOPED")
        target_index = next(i for i, row in enumerate(rows)
                            if row["policy"] == "STATIC_RESERVATION"
                            and row["overhead_units"] == 0)

        changed = copy.deepcopy(rows)
        changed[target_index]["input"]["controls"].pop()
        self.assertTrue(auditor.audit(changed, refusals, fixture)["errors"])

        changed = copy.deepcopy(rows)
        changed[target_index]["events"].append(copy.deepcopy(changed[target_index]["events"][-1]))
        self.assertTrue(auditor.audit(changed, refusals, fixture)["errors"])

        changed = copy.deepcopy(rows)
        changed[target_index]["summary"]["control_completed"] += 1
        self.assertTrue(auditor.audit(changed, refusals, fixture)["errors"])

        changed = copy.deepcopy(rows)
        boundary_case = copy.deepcopy(fixture["cases"][0])
        boundary_case["case_id"] = "mutation-boundary"
        boundary_case["controls"] = [
            {"id": "c0", "class": "control", "stream": "s0",
             "release_choices": [8], "actual_release": 8,
             "min_interarrival": 1, "wcet": 1,
             "relative_deadline": 2, "preemptible": True},
            {"id": "c1", "class": "control", "stream": "s1",
             "release_choices": [8], "actual_release": 8,
             "min_interarrival": 1, "wcet": 1,
             "relative_deadline": 2, "preemptible": True},
        ]
        boundary_case["positive_slack_subset"] = False
        boundary_fixture = copy.deepcopy(fixture)
        boundary_fixture["cases"] = [boundary_case]
        boundary_rows, boundary_refusals = candidate.run(boundary_fixture)
        changed_boundary = copy.deepcopy(boundary_rows)
        boundary_index = next(i for i, row in enumerate(changed_boundary)
                              if row["policy"] == "STATIC_RESERVATION"
                              and row["overhead_units"] == 0)
        event = next(e for e in changed_boundary[boundary_index]["events"] if e["tick"] == 9)
        event["control_used_before"] = 0
        self.assertTrue(auditor.audit(changed_boundary, boundary_refusals, boundary_fixture)["errors"])

        changed = copy.deepcopy(rows)
        raw_case = changed[target_index]["input"]
        raw_case["controls"][0]["class"] = "unrecognized"
        self.assertEqual(auditor.classify(raw_case["controls"][0]), "REJECT_INVALID_JOB_CLASS")
        self.assertTrue(auditor.audit(changed, refusals, fixture)["errors"])


if __name__ == "__main__":
    unittest.main()
