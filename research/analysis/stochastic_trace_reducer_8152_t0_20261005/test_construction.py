import unittest

from audit import audit, cp_lower, cp_upper, outcome
from simulator import legal, one_sided_lower as candidate_lower, one_sided_upper as candidate_upper
from spec import exact_spec


FREEZE = "a" * 64


def small_spec():
    spec = exact_spec()
    spec["instances"] = 1
    spec["baseline_repetitions"] = 8
    spec["confirmation_repetitions_per_stratum"] = 8
    spec["fixed_repetitions_per_candidate"] = 1
    spec["sequential_minimum"] = spec["sequential_maximum"] = spec["sequential_increment"] = 1
    spec["removal_groups"] = spec["removal_groups"][:1]
    return spec


def valid_raw():
    spec = small_spec()
    rows = []
    for method in ("single_run", "fixed_64", "sequential"):
        baseline = []
        for i in range(spec["baseline_repetitions"]):
            seed = 100_000 + i
            events = list(spec["base_trace"])
            fp = outcome(events, seed, 0, spec)
            baseline.append({"seed": seed, "stratum": 0, "events": events,
                             "fingerprint": fp, "stage": "baseline",
                             "exit_code": 17 if fp in (spec["target_fingerprint"], spec["competing_fingerprint"]) else 0})
        successes = sum(x["fingerprint"] == spec["target_fingerprint"] for x in baseline)
        lower = cp_lower(successes, len(baseline), spec["familywise_alpha"] / 2)
        threshold = max(0.0, lower-spec["noninferiority_margin"])
        group_name, removed = spec["removal_groups"][0]
        proposed = [e for e in spec["base_trace"] if e not in removed]
        seed = 3_000_000
        while outcome(proposed, seed, 0, spec) == spec["target_fingerprint"]:
            seed += 1
        fp = outcome(proposed, seed, 0, spec)
        candidate = {"seed": seed, "stratum": 0, "events": proposed,
                     "fingerprint": fp, "exit_code": 17 if fp in (spec["target_fingerprint"], spec["competing_fingerprint"]) else 0,
                     "stage": "search", "group": group_name}
        candidate_success = int(candidate["fingerprint"] == spec["target_fingerprint"])
        look_alpha = spec["familywise_alpha"]/(len(spec["removal_groups"])*2)
        lo, hi = cp_lower(candidate_success, 1, look_alpha), cp_upper(candidate_success, 1, look_alpha)
        decision = {"single_run": "REJECT_ONE_MISS", "fixed_64": "REJECT_FIXED_BOUND",
                    "sequential": "REJECT_SEQUENTIAL_BOUND" if hi < threshold else "REJECT_INCONCLUSIVE"}[method]
        attempts = [{"group": group_name, "decision": decision, "n": 1,
                    "trace_before": list(spec["base_trace"]), "trace_after": list(spec["base_trace"]),
                    "proposed_trace": proposed, "threshold": threshold,
                    "looks": [{"n": 1, "successes": candidate_success,
                               "lower": None if method == "single_run" else lo,
                               "upper": None if method == "single_run" else hi}],
                    "raw_trial_start": 0, "raw_trial_count": 1}]
        confirmation = []
        for j in range(spec["confirmation_repetitions_per_stratum"]):
            seed = 10_000_000+j
            fp = outcome(spec["base_trace"], seed, 0, spec)
            confirmation.append({"stratum": 0, "seed": seed, "original_fingerprint": fp,
                                 "final_fingerprint": fp, "delta": 0})
        rows.append({"method": method, "instance": 0, "stratum": 0,
                     "baseline_trials": baseline, "baseline_target_successes": successes,
                     "baseline_lower_bound": lower, "screen_threshold": threshold,
                     "candidate_trials": [candidate], "attempts": attempts,
                     "initial_trace": list(spec["base_trace"]), "final_trace": list(spec["base_trace"]),
                     "confirmations": confirmation})
    return {"schema": "unjuno.issue8152.candidate.raw.v1", "freeze_digest": FREEZE,
            "expected_freeze_digest": FREEZE, "runs": rows}


class ConstructionTests(unittest.TestCase):
    def test_authority_and_release_are_hard_requirements(self):
        spec = exact_spec()
        for missing in ("lease", "release"):
            trace = [e for e in spec["base_trace"] if e != missing]
            self.assertEqual(outcome(trace, 123, 0, spec), "INVALID_AUTHORITY_OR_DEPENDENCY")

    def test_competing_fingerprint_is_not_target_even_with_shared_exit_code(self):
        spec = exact_spec()
        self.assertEqual(spec["same_exit_code"], 17)
        trace = list(spec["base_trace"])
        for seed in range(10_000):
            observed = outcome(trace, seed, 0, spec)
            if observed == spec["competing_fingerprint"]:
                break
        else:
            self.fail("fixed fixture has no competing-fingerprint seed")
        self.assertEqual(observed, "COMPETING_WIDGET_CRASH")
        self.assertNotEqual(spec["target_fingerprint"], observed)

    def test_independent_valid_raw_fixture_audits(self):
        report = audit(valid_raw(), spec=small_spec(), expected_freeze_digest=FREEZE)
        self.assertTrue(report["valid"], report["errors"])

    def test_confirmation_seed_reuse_is_rejected(self):
        raw = valid_raw()
        raw["runs"][0]["confirmations"][0]["seed"] = raw["runs"][0]["candidate_trials"][0]["seed"]
        report = audit(raw, spec=small_spec(), expected_freeze_digest=FREEZE)
        self.assertIn("search_confirmation_seed_overlap", report["errors"])

    def test_frozen_threshold_mutation_is_rejected(self):
        raw = valid_raw()
        raw["runs"][0]["screen_threshold"] += 0.1
        report = audit(raw, spec=small_spec(), expected_freeze_digest=FREEZE)
        self.assertIn("baseline_gate_mismatch", report["errors"])

    def test_candidate_threshold_mutation_is_rejected(self):
        raw = valid_raw()
        raw["runs"][0]["attempts"][0]["threshold"] += 0.1
        report = audit(raw, spec=small_spec(), expected_freeze_digest=FREEZE)
        self.assertIn("candidate_proposal_or_threshold_mismatch", report["errors"])

    def test_omitted_raw_attempt_row_is_rejected(self):
        raw = valid_raw()
        raw["runs"][0]["candidate_trials"].clear()
        report = audit(raw, spec=small_spec(), expected_freeze_digest=FREEZE)
        self.assertIn("omitted_raw_attempt", report["errors"])

    def test_freeze_digest_mismatch_is_rejected(self):
        raw = valid_raw()
        report = audit(raw, spec=small_spec(), expected_freeze_digest="b"*64)
        self.assertIn("freeze_digest_mismatch", report["errors"])

    def test_interval_endpoints(self):
        self.assertEqual(cp_lower(0, 10, 0.05), 0.0)
        self.assertEqual(cp_upper(10, 10, 0.05), 1.0)
        self.assertLess(cp_lower(8, 10, 0.05), cp_upper(8, 10, 0.05))

    def test_independent_interval_implementations_agree(self):
        for n, k in ((8, 2), (64, 47), (512, 380)):
            alpha = 0.00025
            self.assertAlmostEqual(cp_lower(k, n, alpha), candidate_lower(k, n, alpha), delta=1e-12)
            self.assertAlmostEqual(cp_upper(k, n, alpha), candidate_upper(k, n, alpha), delta=1e-12)

    def test_event_grammar_rejects_unknown_or_duplicate_events(self):
        base = list(exact_spec()["base_trace"])
        self.assertFalse(legal(base+["untyped_event"]))
        self.assertFalse(legal(base+["reset"]))


if __name__ == "__main__":
    unittest.main()
