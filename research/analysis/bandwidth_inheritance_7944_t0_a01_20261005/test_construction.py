"""Pre-freeze behavior checks; these are not the formal allocation."""
import importlib.util
import copy
import json
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent


def candidate_module(test):
    path = HERE / "candidate.py"
    test.assertTrue(path.is_file(), "candidate.py must implement the tested scheduler")
    spec = importlib.util.spec_from_file_location("bwi_candidate", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def auditor_module(test):
    path = HERE / "audit.py"
    test.assertTrue(path.is_file(), "audit.py must independently reconstruct the candidate trace")
    spec = importlib.util.spec_from_file_location("bwi_audit", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def inversion_case():
    return {
        "case_id": "budget_inversion",
        "horizon": 12,
        "resource": "verification-slot",
        "servers": [
            {"id": "W", "q": 2, "p": 6, "budget": 2, "deadline": 6,
             "tie_rank": 0},
            {"id": "H", "q": 1, "p": 6, "budget": 0, "deadline": 6,
             "tie_rank": 1},
            {"id": "BE", "q": 1, "p": 6, "budget": 1, "deadline": 6,
             "tie_rank": 2},
        ],
        "jobs": [
            {"id": "holder", "server": "H", "release": 0, "work": 1,
             "deadline": 12, "holds": ["verification-slot"]},
            {"id": "verifier", "server": "W", "release": 0, "work": 1,
             "deadline": 4, "waits_for": "verification-slot",
             "edge": {"authenticated": True, "current": True, "complete": True,
                      "resource_preemptible": True, "expires": 4}},
            {"id": "best-effort", "server": "BE", "release": 0, "work": 1,
             "deadline": 12},
        ],
    }


class BudgetInheritanceConstructionTests(unittest.TestCase):
    def test_independent_reconstruction_and_mutations_fail_closed(self):
        c = candidate_module(self)
        a = auditor_module(self)
        fixture = json.loads((HERE / "fixture.json").read_text())
        raw_runs = [c.simulate(case, policy) for case in fixture["cases"]
                    for policy in ("NONE", "PI_HOME_CHARGED", "BWI")]
        raw = {"runs": raw_runs}
        self.assertEqual(a.validate_runs(raw, fixture), [])
        for mutation in ("budget_refund", "duplicate_cpu_service", "wrong_server_charge",
                         "stale_freshness_admission", "omitted_policy_case"):
            damaged = copy.deepcopy(raw)
            target = next(run for run in damaged["runs"]
                          if run["case_id"] == "budget_inversion" and run["policy"] == "BWI")
            if mutation == "budget_refund":
                target["events"][0]["budget_after"] += 1
            elif mutation == "duplicate_cpu_service":
                target["events"].append(copy.deepcopy(target["events"][0]))
            elif mutation == "wrong_server_charge":
                target["events"][0]["server_charged"] = "H"
            elif mutation == "stale_freshness_admission":
                target = next(run for run in damaged["runs"]
                              if run["case_id"] == "budget_inversion" and run["policy"] == "NONE")
                target["freshness"]["verifier"] = "ADMITTED_FRESH"
            else:
                damaged["runs"].pop()
            self.assertTrue(a.validate_runs(damaged, fixture), mutation)

    def test_frozen_matrix_discriminates_policy_and_fail_closed_controls(self):
        c = candidate_module(self)
        fixture = json.loads((HERE / "fixture.json").read_text())
        self.assertEqual(fixture["schema"], "issue7944-bwi-t0-a01-fixture-v1")
        for case in fixture["cases"]:
            self.assertLessEqual(sum(server["q"] / server["p"]
                                     for server in case["servers"]), 1.0)
        cases = {case["case_id"]: case for case in fixture["cases"]}
        results = {
            case_id: {policy: c.simulate(copy.deepcopy(cases[case_id]), policy)
                      for policy in ("NONE", "PI_HOME_CHARGED", "BWI")}
            for case_id in cases
        }
        inversion = results["budget_inversion"]
        self.assertEqual(inversion["BWI"]["job_completion"]["verifier"], 2)
        self.assertEqual(inversion["BWI"]["deadline_misses"], [])
        self.assertEqual(inversion["BWI"]["job_completion"]["best-effort"], 3)
        self.assertEqual(inversion["PI_HOME_CHARGED"]["job_completion"]["verifier"], 8)
        self.assertIn("verifier", inversion["NONE"]["deadline_misses"])
        for policy in ("NONE", "PI_HOME_CHARGED", "BWI"):
            self.assertEqual(results["no_contention"][policy]["job_completion"]["verifier"], 1)
            self.assertEqual(results["no_contention"][policy]["inherited_ticks"], 0)
        no_contention_runs = [results["no_contention"][policy] for policy in
                              ("NONE", "PI_HOME_CHARGED", "BWI")]
        normalized = [{k: v for k, v in run.items() if k != "policy"}
                      for run in no_contention_runs]
        self.assertEqual(normalized[0], normalized[1])
        self.assertEqual(normalized[1], normalized[2])
        exhausted = results["waiter_budget_exhaustion"]["BWI"]
        self.assertEqual(exhausted["inherited_ticks"], 1)
        self.assertIn("verifier", exhausted["deadline_misses"])
        self.assertEqual(results["unlock_at_replenishment_boundary"]["BWI"]
                         ["job_completion"]["verifier"], 4)
        waiters = results["two_waiters"]["BWI"]
        self.assertEqual(waiters["inherited_ticks"], 1)
        self.assertEqual(waiters["events"][0]["donor"], "waiter1")
        nested = results["nested_acyclic_chain"]["BWI"]
        self.assertEqual(nested["job_completion"]["verifier"], 3)
        self.assertEqual([e["job"] for e in nested["events"]], ["h2", "h1", "verifier"])
        cycle = results["dependency_cycle"]["BWI"]
        self.assertEqual(cycle["inherited_ticks"], 0)
        self.assertIn("DEPENDENCY_CYCLE", {d["reason"] for d in cycle["decisions"]})
        cancelled = results["cancelled_waiter"]["BWI"]
        self.assertEqual(cancelled["inherited_ticks"], 0)
        self.assertEqual(cancelled["cancelled_jobs"], ["verifier"])
        remote = results["remote_nonpreemptible_resource"]["BWI"]
        self.assertEqual(remote["inherited_ticks"], 0)
        self.assertIn("UNSUPPORTED_RESOURCE", {d["reason"] for d in remote["decisions"]})

    def test_bwi_spends_waiter_budget_once_and_meets_freshness_deadline(self):
        c = candidate_module(self)
        result = c.simulate(inversion_case(), "BWI")
        self.assertEqual(result["job_completion"]["verifier"], 2)
        self.assertEqual(result["deadline_misses"], [])
        self.assertEqual(result["server_ticks"]["W"], 2)
        self.assertEqual(result["server_ticks"]["H"], 0)
        self.assertEqual(result["inherited_ticks"], 1)

    def test_priority_inheritance_cannot_spend_an_exhausted_home_server(self):
        c = candidate_module(self)
        result = c.simulate(inversion_case(), "PI_HOME_CHARGED")
        self.assertEqual(result["job_completion"]["verifier"], 8)
        self.assertEqual(result["deadline_misses"], ["verifier"])
        self.assertEqual(result["inherited_ticks"], 0)

    def test_no_inheritance_does_not_create_an_inherited_charge(self):
        c = candidate_module(self)
        result = c.simulate(inversion_case(), "NONE")
        self.assertEqual(result["job_completion"]["verifier"], 8)
        self.assertEqual(result["inherited_ticks"], 0)

    def test_unverified_or_expired_wait_edges_fail_closed(self):
        c = candidate_module(self)
        a = auditor_module(self)
        for key, value, reason in (
            ("authenticated", False, "UNAUTHENTICATED_EDGE"),
            ("current", False, "STALE_EDGE"),
            ("complete", False, "INCOMPLETE_EDGE"),
            ("resource_preemptible", False, "UNSUPPORTED_RESOURCE"),
            ("expires", 0, "EXPIRED_EDGE"),
        ):
            case = inversion_case()
            case["jobs"][1]["edge"][key] = value
            result = c.simulate(case, "BWI")
            self.assertEqual(result["inherited_ticks"], 0, key)
            self.assertIn(reason, {d["reason"] for d in result["decisions"]}, key)
            self.assertIn("verifier", result["deadline_misses"], key)
            self.assertEqual(result, a.reconstruct(case, "BWI"), key)

    def test_boundary_unlock_precedes_same_tick_replenishment_use(self):
        c = candidate_module(self)
        case = {
            "case_id": "boundary_unlock", "horizon": 8,
            "servers": [
                {"id": "W", "q": 1, "p": 3, "budget": 1, "deadline": 3, "tie_rank": 0},
                {"id": "H", "q": 1, "p": 3, "budget": 0, "deadline": 3, "tie_rank": 1},
                {"id": "BE", "q": 1, "p": 3, "budget": 1, "deadline": 3, "tie_rank": 2},
            ],
            "jobs": [
                {"id": "holder", "server": "H", "release": 2, "work": 1,
                 "deadline": 8, "holds": ["r"]},
                {"id": "verifier", "server": "W", "release": 2, "work": 1,
                 "deadline": 5, "waits_for": "r",
                 "edge": {"authenticated": True, "current": True, "complete": True,
                          "resource_preemptible": True, "expires": 5}},
            ],
        }
        result = c.simulate(case, "BWI")
        self.assertEqual(result["job_completion"]["verifier"], 4)
        self.assertEqual(result["server_ticks"]["W"], 2)

    def test_nested_chain_debits_only_selected_waiter_server(self):
        c = candidate_module(self)
        case = {
            "case_id": "nested_chain", "horizon": 16,
            "servers": [
                {"id": "W", "q": 3, "p": 6, "budget": 3, "deadline": 6, "tie_rank": 0},
                {"id": "H1", "q": 1, "p": 6, "budget": 0, "deadline": 6, "tie_rank": 1},
                {"id": "H2", "q": 1, "p": 6, "budget": 0, "deadline": 6, "tie_rank": 1},
            ],
            "jobs": [
                {"id": "h1", "server": "H1", "release": 0, "work": 1,
                 "deadline": 16, "holds": ["r1"], "waits_for": "r2"},
                {"id": "h2", "server": "H2", "release": 0, "work": 1,
                 "deadline": 16, "holds": ["r2"]},
                {"id": "verifier", "server": "W", "release": 0, "work": 1,
                 "deadline": 4, "waits_for": "r1",
                 "edge": {"authenticated": True, "current": True, "complete": True,
                          "resource_preemptible": True, "expires": 4}},
            ],
        }
        result = c.simulate(case, "BWI")
        self.assertEqual(result["job_completion"]["verifier"], 3, result)
        self.assertEqual(result["inherited_ticks"], 2)
        self.assertEqual(result["server_ticks"], {"H1": 0, "H2": 0, "W": 3})
        self.assertEqual([e["job"] for e in result["events"]], ["h2", "h1", "verifier"])

    def test_no_contention_is_policy_invariant(self):
        c = candidate_module(self)
        case = inversion_case()
        case["case_id"] = "no_contention"
        verifier = case["jobs"][1]
        verifier.pop("waits_for")
        verifier.pop("edge")
        outputs = [c.simulate(copy.deepcopy(case), policy)
                   for policy in ("NONE", "PI_HOME_CHARGED", "BWI")]
        self.assertEqual([o["job_completion"]["verifier"] for o in outputs], [1, 1, 1])
        self.assertEqual([o["inherited_ticks"] for o in outputs], [0, 0, 0])

    def test_inherited_execution_stops_at_waiter_budget_exhaustion(self):
        c = candidate_module(self)
        case = inversion_case()
        case["case_id"] = "waiter_budget_exhaustion"
        case["servers"][0].update(q=1, budget=1)
        case["jobs"][0]["work"] = 2
        case["horizon"] = 20
        result = c.simulate(case, "BWI")
        self.assertEqual(result["inherited_ticks"], 1)
        self.assertEqual(result["server_ticks"]["W"], 2)
        self.assertIn("verifier", result["deadline_misses"])

    def test_cancelled_waiter_cannot_donate(self):
        c = candidate_module(self)
        case = inversion_case()
        case["jobs"][1]["cancel_at"] = 0
        result = c.simulate(case, "BWI")
        self.assertEqual(result["inherited_ticks"], 0)
        self.assertEqual(result["cancelled_jobs"], ["verifier"])

    def test_cycle_refuses_inheritance(self):
        c = candidate_module(self)
        case = {
            "case_id": "cycle", "horizon": 8,
            "servers": [
                {"id": "W", "q": 2, "p": 6, "budget": 2, "deadline": 6, "tie_rank": 0},
                {"id": "H1", "q": 1, "p": 6, "budget": 0, "deadline": 6, "tie_rank": 1},
                {"id": "H2", "q": 1, "p": 6, "budget": 0, "deadline": 6, "tie_rank": 1},
            ],
            "jobs": [
                {"id": "h1", "server": "H1", "release": 0, "work": 1,
                 "deadline": 8, "holds": ["r1"], "waits_for": "r2"},
                {"id": "h2", "server": "H2", "release": 0, "work": 1,
                 "deadline": 8, "holds": ["r2"], "waits_for": "r1"},
                {"id": "verifier", "server": "W", "release": 0, "work": 1,
                 "deadline": 4, "waits_for": "r1",
                 "edge": {"authenticated": True, "current": True, "complete": True,
                          "resource_preemptible": True, "expires": 4}},
            ],
        }
        result = c.simulate(case, "BWI")
        self.assertEqual(result["inherited_ticks"], 0)
        self.assertIn("DEPENDENCY_CYCLE", {d["reason"] for d in result["decisions"]})


if __name__ == "__main__":
    unittest.main(verbosity=2)
