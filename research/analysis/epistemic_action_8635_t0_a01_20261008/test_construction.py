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
        for seed in (59, 71):
            for item in generate_cases(seed):
                cases.append({"case_id": item["case_id"], "input": item["input"], "prescription": item["truth"]["epistemic_action"]})
        rows = run_trials(cases)

        self.assertEqual(len(rows), 360)
        self.assertEqual(len({(row["case_id"], row["policy"], row["arm"]) for row in rows}), 360)


class DataPartitionTests(unittest.TestCase):
    def test_fixture_omits_truth_and_oracle_retains_all_held_out_cases(self):
        from .prepare_data import build_dataset

        fixture, oracle = build_dataset((59, 71, 83, 97))

        self.assertEqual(len(fixture["cases"]), 48)
        self.assertEqual(len(oracle["cases"]), 48)
        self.assertNotIn("truth", fixture["cases"][0])
        self.assertNotIn("truth", fixture["cases"][0]["input"])
        self.assertEqual(oracle["cases"]["S59-C00"]["need"], "NEEDS_ACQUISITION")
        self.assertEqual(len(set(oracle["cases"])), 48)


class IndependentAuditorTests(unittest.TestCase):
    def setUp(self):
        from .candidate import run_trials
        from .prepare_data import build_dataset

        self.fixture, self.oracle = build_dataset((59, 71, 83, 97))
        self.raw = {"schema": "epistemic-action-8635-candidate-v1", "rows": run_trials(self.fixture["cases"])}

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
    def test_runner_preserves_launch_failure_without_retry_or_auditor(self):
        import hashlib
        import json
        import sys
        from pathlib import Path
        from tempfile import TemporaryDirectory
        from unittest.mock import patch

        from . import run_formal
        from .prepare_data import build_dataset

        with TemporaryDirectory() as temporary:
            root = Path(temporary) / "source"
            root.mkdir()
            fixture, oracle = build_dataset((59, 71, 83, 97))
            sources = {
                "candidate.py": b"candidate",
                "policies.py": b"policies",
                "fixture.json": json.dumps(fixture).encode(),
                "auditor.py": b"auditor",
                "oracle.json": json.dumps(oracle).encode(),
            }
            hashes = {}
            for name, content in sources.items():
                (root / name).write_bytes(content)
                hashes[name] = hashlib.sha256(content).hexdigest()
            (root / "FREEZE.json").write_text(json.dumps({"files": hashes, "image": "python@sha256:" + "a" * 64}), encoding="utf-8")
            output = Path(temporary) / "formal"
            launch_error = FileNotFoundError("synthetic missing executable")
            with patch("subprocess.run", side_effect=launch_error) as run_mock:
                receipt = run_formal.run_once(root, output, "missing-wslc.exe")
            run_mock.assert_called_once()

            receipt_path = output / "RUN.json"
            self.assertTrue(receipt_path.exists())
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            self.assertEqual(receipt["candidate_invocations"], 0)
            self.assertEqual(receipt["auditor_invocations"], 0)
            self.assertEqual(receipt["retries"], 0)
            self.assertEqual(receipt["formal_disposition"], "HOLD")
            self.assertIn("launch_error", receipt)
            self.assertTrue((output / "candidate.stderr").exists())
            self.assertTrue((output / "raw_audit.json").exists())

    def test_container_stages_keep_oracle_and_candidate_source_separate(self):
        from pathlib import Path
        from tempfile import TemporaryDirectory
        from .run_formal import prepare_auditor_stage, prepare_candidate_stage

        with TemporaryDirectory() as temporary:
            root = Path(temporary) / "source"
            root.mkdir()
            for name in ("candidate.py", "policies.py", "fixture.json", "auditor.py", "oracle.json"):
                (root / name).write_text(name, encoding="utf-8")
            candidate_stage = Path(temporary) / "candidate"
            auditor_stage = Path(temporary) / "auditor"

            prepare_candidate_stage(root, candidate_stage)
            prepare_auditor_stage(root, auditor_stage, b'{"rows":[]}\n')

            self.assertEqual(sorted(path.name for path in candidate_stage.iterdir()), ["candidate.py", "fixture.json", "policies.py"])
            self.assertEqual(sorted(path.name for path in auditor_stage.iterdir()), ["auditor.py", "fixture.json", "oracle.json", "raw_candidate.json"])
            self.assertFalse((auditor_stage / "candidate.py").exists())
            self.assertFalse((candidate_stage / "oracle.json").exists())
            self.assertEqual((auditor_stage / "raw_candidate.json").read_bytes(), b'{"rows":[]}\n')

    def test_wslc_command_pins_offline_cpu_only_readonly_candidate_stage(self):
        from .run_formal import build_wslc_command

        command = build_wslc_command(
            "wslc.exe",
            "python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f",
            "epistemic-8635-candidate-a01",
            r"C:\research\candidate stage",
            "candidate.py",
            "/src/fixture.json",
        )

        self.assertEqual(command, [
            "wslc.exe", "run", "--rm", "--pull", "never", "--network", "none",
            "--cpus", "1", "--user", "65534:65534", "--name", "epistemic-8635-candidate-a01",
            "--mount", r"type=bind,source=C:\research\candidate stage,target=/src,readonly",
            "--workdir", "/src",
            "python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f",
            "python", "/src/candidate.py", "/src/fixture.json",
        ])

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


class CandidateCliIntegrationTests(unittest.TestCase):
    def test_frozen_candidate_cli_emits_720_new_allocation_rows(self):
        import json
        import subprocess
        import sys
        from pathlib import Path
        from tempfile import TemporaryDirectory

        from . import candidate
        from .prepare_data import build_dataset

        fixture, _ = build_dataset((59, 71, 83, 97))
        with TemporaryDirectory() as temporary:
            fixture_path = Path(temporary) / "fixture.json"
            fixture_path.write_text(json.dumps(fixture), encoding="utf-8")
            completed = subprocess.run(
                [sys.executable, str(Path(candidate.__file__).resolve()), str(fixture_path)],
                capture_output=True,
                check=False,
            )

        self.assertEqual(completed.returncode, 0, completed.stderr.decode("utf-8", errors="replace"))
        self.assertEqual(completed.stderr, b"")
        result = json.loads(completed.stdout)
        self.assertEqual(result["schema"], "epistemic-action-8635-candidate-v1")
        self.assertEqual(len(result["rows"]), 720)
        self.assertEqual(len({(row["case_id"], row["policy"], row["arm"]) for row in result["rows"]}), 720)


class AuditorCliIntegrationTests(unittest.TestCase):
    def test_raw_only_auditor_cli_reads_saved_candidate_bytes(self):
        import json
        import subprocess
        import sys
        from pathlib import Path
        from tempfile import TemporaryDirectory

        from . import auditor, candidate
        from .prepare_data import build_dataset

        fixture, oracle = build_dataset((59, 71, 83, 97))
        raw = {"schema": "epistemic-action-8635-candidate-v1", "rows": candidate.run_trials(fixture["cases"])}
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            fixture_path = root / "fixture.json"
            oracle_path = root / "oracle.json"
            raw_path = root / "raw_candidate.json"
            fixture_path.write_text(json.dumps(fixture), encoding="utf-8")
            oracle_path.write_text(json.dumps(oracle), encoding="utf-8")
            raw_path.write_text(json.dumps(raw), encoding="utf-8")
            completed = subprocess.run(
                [sys.executable, str(Path(auditor.__file__).resolve()), "--fixture", str(fixture_path), "--oracle", str(oracle_path), "--candidate", str(raw_path)],
                capture_output=True,
                check=False,
            )

        self.assertEqual(completed.returncode, 0, completed.stderr.decode("utf-8", errors="replace"))
        self.assertEqual(completed.stderr, b"")
        result = json.loads(completed.stdout)
        self.assertEqual(result["schema"], "epistemic-action-8635-audit-v1")
        self.assertEqual(result["method_disposition"], "PASS_METHOD_SCOPED")
        self.assertEqual(result["rows_reconstructed"], 720)
        self.assertEqual(result["errors"], [])


if __name__ == "__main__":
    unittest.main()
