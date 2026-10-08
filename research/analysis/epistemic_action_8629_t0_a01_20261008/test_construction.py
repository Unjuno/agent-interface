import unittest


class HeldOutGeneratorContractTests(unittest.TestCase):
    def test_generator_returns_seed_bound_blinded_cases(self):
        from .generator import generate_cases

        cases = generate_cases(17)

        self.assertEqual(len(cases), 12)
        self.assertEqual(cases[0]["case_id"], "S17-C00")
        self.assertEqual(cases[0]["input"]["allowed_actions"], ["ACQUIRE", "COMMIT", "YIELD"])
        self.assertNotIn("stratum", cases[0]["input"])
        self.assertNotIn("expected_decision", cases[0]["input"])
        self.assertEqual(len({case["case_id"] for case in cases}), 12)

    def test_held_out_seeds_change_permuted_observation_surface(self):
        from .generator import generate_cases

        first = generate_cases(17)
        second = generate_cases(29)

        self.assertEqual([case["case_id"] for case in first], [f"S17-C{i:02d}" for i in range(12)])
        self.assertNotEqual(first[0]["input"]["evidence"]["provenance"], second[0]["input"]["evidence"]["provenance"])

    def test_case_input_and_truth_are_separate_with_observable_evidence_states(self):
        from .generator import generate_cases

        cases = generate_cases(17)

        self.assertEqual(cases[0].get("input", {}).get("evidence"), {
            "complete": False,
            "decision_set": ["APPROVE", "DENY"],
            "provenance": ["receipt-17-00"],
            "representation_usable": True,
        })
        self.assertEqual(cases[0]["truth"]["decision"], "APPROVE")
        self.assertEqual(cases[0]["truth"].get("need"), "NEEDS_ACQUISITION")
        self.assertNotIn("truth", cases[0]["input"])
        self.assertNotIn("stratum", cases[0]["input"])
        self.assertEqual(cases[0]["input"]["allowed_actions"], ["ACQUIRE", "COMMIT", "YIELD"])

    def test_acquisition_receipt_is_seed_bound_and_narrows_decision_set(self):
        from .generator import generate_cases

        acquired = generate_cases(17)[0]["input"].get("action_responses", {}).get("ACQUIRE", {})

        self.assertEqual(acquired, {
            "evidence": {
                "complete": True,
                "decision_set": ["APPROVE"],
                "provenance": ["receipt-17-00", "acquired-17-00"],
                "representation_usable": True,
            },
            "safe": True,
        })


class PolicySelectionTests(unittest.TestCase):
    def test_reference_policy_selects_safe_evidence_action_or_stops(self):
        from .generator import generate_cases
        from .policies import select_action

        cases = generate_cases(17)
        expected = ["ACQUIRE", "TRANSFORM", "PROBE", "COMMIT", "YIELD", "YIELD"]
        for family, want in enumerate(expected):
            with self.subTest(family=family):
                self.assertEqual(select_action(cases[family * 2]["input"], "REFERENCE", "AVAILABLE"), want)

    def test_no_action_arm_yields_when_evidence_is_insufficient(self):
        from .generator import generate_cases
        from .policies import select_action

        case_input = generate_cases(17)[0]["input"]

        self.assertEqual(select_action(case_input, "REFERENCE", "NO_EPISTEMIC_ACTION"), "YIELD")

    def test_stopping_defect_is_observable_without_changing_the_decision(self):
        from .generator import generate_cases
        from .policies import select_action

        sufficient = generate_cases(17)[6]["input"]

        self.assertEqual(select_action(sufficient, "REFERENCE", "AVAILABLE"), "COMMIT")
        self.assertEqual(select_action(sufficient, "STOPPING_DEFECT", "AVAILABLE"), "PROBE")

    def test_selection_defect_abstains_despite_a_safe_available_action(self):
        from .generator import generate_cases
        from .policies import select_action

        missing = generate_cases(17)[0]["input"]

        self.assertEqual(select_action(missing, "ACTION_SELECTION_DEFECT", "AVAILABLE"), "YIELD")


class CandidateExecutionTests(unittest.TestCase):
    def test_candidate_uses_action_receipt_without_access_to_oracle(self):
        from .candidate import run_trial
        from .generator import generate_cases

        generated = generate_cases(17)[0]
        case = {"case_id": generated["case_id"], "input": generated["input"], "prescription": "ACQUIRE"}
        actual = run_trial(case, "REFERENCE", "AVAILABLE")

        self.assertEqual(actual.get("selected_action"), "ACQUIRE")
        self.assertEqual(actual.get("evidence_after", {}).get("decision_set"), ["APPROVE"])
        self.assertEqual(actual.get("final_decision"), "APPROVE")
        self.assertNotIn("truth", actual)

    def test_prescribed_and_available_arms_keep_distinct_action_access(self):
        from .candidate import run_trial
        from .generator import generate_cases

        generated = generate_cases(17)[0]
        case = {"case_id": generated["case_id"], "input": generated["input"], "prescription": "ACQUIRE"}

        self.assertEqual(run_trial(case, "REFERENCE", "PRESCRIBED").get("selected_action"), "ACQUIRE")
        self.assertEqual(run_trial(case, "REFERENCE", "NO_EPISTEMIC_ACTION").get("selected_action"), "YIELD")

    def test_recognition_and_evidence_use_defects_have_separate_signatures(self):
        from .candidate import run_trial
        from .generator import generate_cases

        generated = generate_cases(17)[0]
        case = {"case_id": generated["case_id"], "input": generated["input"], "prescription": "ACQUIRE"}
        recognized = run_trial(case, "RECOGNITION_DEFECT", "AVAILABLE")
        unused = run_trial(case, "EVIDENCE_USE_DEFECT", "AVAILABLE")

        self.assertEqual(recognized["recognized_need"], "UNKNOWN")
        self.assertEqual(recognized["selected_action"], "ACQUIRE")
        self.assertEqual(unused["evidence_after"]["decision_set"], ["APPROVE"])
        self.assertEqual(unused["final_decision"], "UNKNOWN")

    def test_run_trials_emits_every_seed_case_policy_and_arm_once(self):
        from .candidate import run_trials
        from .generator import generate_cases

        cases = []
        for seed in (17, 29):
            for item in generate_cases(seed):
                cases.append({"case_id": item["case_id"], "input": item["input"], "prescription": item["truth"]["epistemic_action"]})
        rows = run_trials(cases)

        self.assertEqual(len(rows), 360)
        self.assertEqual(len({(row["case_id"], row["policy"], row["arm"]) for row in rows}), 360)


class DataPartitionTests(unittest.TestCase):
    def test_fixture_omits_truth_and_oracle_retains_all_held_out_cases(self):
        from .prepare_data import build_dataset

        fixture, oracle = build_dataset((17, 29, 41, 53))

        self.assertEqual(len(fixture["cases"]), 48)
        self.assertEqual(len(oracle["cases"]), 48)
        self.assertNotIn("truth", fixture["cases"][0])
        self.assertNotIn("truth", fixture["cases"][0]["input"])
        self.assertEqual(oracle["cases"]["S17-C00"]["need"], "NEEDS_ACQUISITION")
        self.assertEqual(len(set(oracle["cases"])), 48)


class IndependentAuditorTests(unittest.TestCase):
    def setUp(self):
        from .candidate import run_trials
        from .prepare_data import build_dataset

        self.fixture, self.oracle = build_dataset((17, 29, 41, 53))
        self.raw = {"schema": "epistemic-action-8629-candidate-v1", "rows": run_trials(self.fixture["cases"])}

    def test_auditor_reconstructs_all_policy_arm_rows(self):
        from .auditor import audit

        result = audit(self.fixture, self.oracle, self.raw)

        self.assertEqual(result["method_disposition"], "PASS_METHOD_SCOPED")
        self.assertEqual(result["rows_reconstructed"], 720)
        self.assertEqual(result["mutation_controls_rejected"], 4)
        self.assertEqual(result.get("hypothesis_gates"), {
            "recognition_defect_detected": True,
            "selection_defect_detected": True,
            "evidence_use_defect_detected": True,
            "stopping_defect_hidden_by_task_success": True,
            "zero_hard_gate_violations": True,
        })

    def test_auditor_rejects_missing_action_provenance_and_decision_mutations(self):
        from copy import deepcopy
        from .auditor import audit

        mutations = []
        missing = deepcopy(self.raw)
        missing["rows"].pop()
        mutations.append(missing)
        action = deepcopy(self.raw)
        action["rows"][0]["selected_action"] = "YIELD"
        mutations.append(action)
        provenance = deepcopy(self.raw)
        provenance["rows"][0]["evidence_after"]["provenance"].append("fabricated")
        mutations.append(provenance)
        decision = deepcopy(self.raw)
        decision["rows"][0]["final_decision"] = "DENY"
        mutations.append(decision)

        for mutated in mutations:
            with self.subTest(rows=len(mutated["rows"])):
                self.assertEqual(audit(self.fixture, self.oracle, mutated)["method_disposition"], "FAIL_METHOD")


class FormalRunnerSafetyTests(unittest.TestCase):
    def test_runner_refuses_source_hash_mismatch_before_execution(self):
        from tempfile import TemporaryDirectory
        from pathlib import Path
        from .run_formal import verify_sources

        with TemporaryDirectory() as tmp:
            source = Path(tmp) / "source.py"
            source.write_bytes(b"frozen bytes")
            import hashlib
            valid = {"source.py": hashlib.sha256(b"frozen bytes").hexdigest()}
            invalid = {"source.py": "0" * 64}

            self.assertEqual(verify_sources(Path(tmp), valid), [])
            self.assertTrue(verify_sources(Path(tmp), invalid))

    def test_runner_refuses_to_overwrite_an_existing_formal_directory(self):
        from tempfile import TemporaryDirectory
        from pathlib import Path
        from .run_formal import reserve_output

        with TemporaryDirectory() as tmp:
            output = Path(tmp) / "formal"
            reserve_output(output)
            with self.assertRaises(FileExistsError):
                reserve_output(output)


if __name__ == "__main__":
    unittest.main()
