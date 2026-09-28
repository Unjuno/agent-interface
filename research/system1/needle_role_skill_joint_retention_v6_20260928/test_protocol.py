"""Zero-fit construction tests for exact launcher and online-window contracts."""
from pathlib import Path
import tempfile
import unittest
import ast
import hashlib
import importlib.util
import sys

import protocol

HERE = Path(__file__).resolve().parent
RESEARCH_ROOT = HERE.parent
RUNNER_PATH = HERE / "runner.py"
AUDIT_PATH = HERE / "audit.py"
FORMAL_PATH = HERE / "formal.py"


class DockerArgvContract(unittest.TestCase):
    def test_realized_argv_matches_exact_frozen_token_array(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source, output = root / "source", root / "fresh-output"
            source.mkdir()
            output.mkdir()
            argv = protocol.docker_argv(source, output)
            self.assertTrue(protocol.exact_argv_matches(argv, list(argv)))
            self.assertEqual(argv.count("--network=none"), 1)
            self.assertIn("--entrypoint=python", argv)
            self.assertIn("-B", argv)
            self.assertIn("/src/runner.py", argv)

    def test_rejects_token_split_missing_extra_reordered_and_mount_mutations(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source, output = root / "source", root / "fresh-output"
            source.mkdir()
            output.mkdir()
            expected = protocol.docker_argv(source, output)
            mutations = []
            split_network = list(expected)
            at = split_network.index("--network=none")
            split_network[at:at + 1] = ["--network", "none"]
            mutations.append(split_network)
            mutations.append(expected[:-1])
            mutations.append(expected + ["--privileged"])
            reordered = list(expected)
            reordered[2], reordered[3] = reordered[3], reordered[2]
            mutations.append(reordered)
            wrong_mount = list(expected)
            mount_index = wrong_mount.index("--mount") + 1
            wrong_mount[mount_index] = wrong_mount[mount_index].replace("target=/src", "dst=/src")
            mutations.append(wrong_mount)
            for actual in mutations:
                self.assertFalse(protocol.exact_argv_matches(actual, expected), actual)

    def test_rejects_aliasing_and_nonexistent_mounts(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source, output = root / "source", root / "source" / "output"
            source.mkdir()
            output.mkdir()
            with self.assertRaisesRegex(ValueError, "disjoint"):
                protocol.docker_argv(source, output)
            with self.assertRaisesRegex(ValueError, "existing directories"):
                protocol.docker_argv(source, root / "missing")


class OnlineWindowContract(unittest.TestCase):
    def setUp(self):
        self.record = {
            "queries": [{"query_id": "q-1", "worker_id": "inference-1",
                         "inference_start_ns": 100, "inference_end_ns": 220,
                         "inference_calls": [{"call_start_ns": 110, "call_end_ns": 160}]}],
            "feedback": [{"feedback_id": "f-1", "query_id": "q-1",
                          "arrived_ns": 120, "consumed_ns": 145,
                          "update_start_ns": 130, "update_end_ns": 180,
                          "trainer_worker_id": "trainer-1"}],
        }

    def test_accepts_new_feedback_consumed_and_updated_inside_live_query(self):
        self.assertEqual(protocol.online_window_errors(self.record), [])

    def test_rejects_precomputed_or_late_feedback(self):
        for arrival in (99, 221):
            mutated = {"queries": [dict(self.record["queries"][0])],
                       "feedback": [dict(self.record["feedback"][0]) ]}
            mutated["feedback"][0]["arrived_ns"] = arrival
            self.assertTrue(protocol.online_window_errors(mutated))

    def test_rejects_nonoverlap_same_worker_and_missing_query(self):
        mutations = []
        late_update = {"queries": [dict(self.record["queries"][0])],
                       "feedback": [dict(self.record["feedback"][0])]}
        late_update["feedback"][0].update(update_start_ns=230, update_end_ns=250,
                                           consumed_ns=240)
        mutations.append(late_update)
        same_worker = {"queries": [dict(self.record["queries"][0])],
                       "feedback": [dict(self.record["feedback"][0])]}
        same_worker["feedback"][0]["trainer_worker_id"] = "inference-1"
        mutations.append(same_worker)
        missing_query = {"queries": [], "feedback": [dict(self.record["feedback"][0])]}
        mutations.append(missing_query)
        for record in mutations:
            self.assertTrue(protocol.online_window_errors(record))

    def test_rejects_wait_only_window_without_overlapping_inference_call(self):
        mutated = {"queries": [dict(self.record["queries"][0])],
                   "feedback": [dict(self.record["feedback"][0])]}
        mutated["queries"][0]["inference_calls"] = [
            {"call_start_ns": 190, "call_end_ns": 210}]
        self.assertTrue(protocol.online_window_errors(mutated))

    def test_rejects_empty_and_malformed_evidence(self):
        self.assertTrue(protocol.online_window_errors({"queries": [], "feedback": []}))
        self.assertTrue(protocol.online_window_errors(None))


class FrozenSourceAndConstructionContract(unittest.TestCase):
    def test_lineage_sources_match_the_registered_frozen_digests(self):
        lineage = HERE / "lineage"
        checks = {
            lineage / "runner.py": "0c978c7721da5f42d57a838a3d141c9781a19a981db5d50b8e028183bc14fcdf",
            lineage / "audit.py": "6abf8cc48d81c5b4267d993e9d992a15d9015f39f0a50558acfcc6d11bcc4558",
            lineage / "FORMAL_FREEZE.json": "482449e97f3b399b166da11fe54a2be2b9df1f13fab1e95753b283614a20cd7c",
        }
        for path, expected in checks.items():
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), expected, str(path))
        self.assertEqual((lineage / "FORMAL_FREEZE.sha256").read_bytes(),
                         (checks[lineage / "FORMAL_FREEZE.json"] + "\n").encode("ascii"))

    def test_runner_and_auditor_load_the_pinned_lineage_without_fitting(self):
        for name in ("runner", "audit"):
            path = HERE / f"{name}.py"
            spec = importlib.util.spec_from_file_location(f"needle_v6_{name}_lineage_test", path)
            module = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = module
            spec.loader.exec_module(module)
            loaded = (module.load_legacy_runner() if name == "runner"
                      else module.load_lineage_auditor())
            self.assertIsNotNone(loaded)

    def test_runner_generates_feedback_after_live_query_start_and_audits_calls(self):
        tree = ast.parse(RUNNER_PATH.read_text(encoding="utf-8"))
        fit = next(node for node in tree.body if isinstance(node, ast.FunctionDef)
                   and node.name == "fit_arm_online")
        calls = [node for node in ast.walk(fit) if isinstance(node, ast.Call)]
        feedback_at = next(node.lineno for node in calls
                           if isinstance(node.func, ast.Name) and node.func.id == "feedback_row")
        first_call_wait_at = next(node.lineno for node in calls
                                  if isinstance(node.func, ast.Attribute)
                                  and node.func.attr == "wait"
                                  and isinstance(node.func.value, ast.Name)
                                  and node.func.value.id == "first_call_started")
        self.assertLess(first_call_wait_at, feedback_at)
        self.assertTrue(any(isinstance(node, ast.Name) and node.id == "online_window_errors"
                            for node in ast.walk(fit)))

    def test_auditor_requires_full_receipt_argv_and_independent_lineage(self):
        source = AUDIT_PATH.read_text(encoding="utf-8")
        tree = ast.parse(source)
        self.assertIn("exact_argv_matches", source)
        self.assertIn("docker_argv", source)
        self.assertNotIn("runner.py\")", source)
        self.assertIn("LEGACY_AUDIT_SHA256", source)
        self.assertTrue(any(isinstance(node, ast.FunctionDef) and node.name == "audit_document"
                            for node in tree.body))

    def test_audit_rejects_nonexact_realized_argv(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source_dir, output_dir = root / "src", root / "out"
            source_dir.mkdir(); output_dir.mkdir()
            expected = protocol.docker_argv(source_dir, output_dir)
            mutated = list(expected) + ["--privileged"]
            self.assertFalse(protocol.exact_argv_matches(mutated, expected))

    def test_formal_launcher_has_only_one_run_call_and_requires_lease_before_it(self):
        tree = ast.parse(FORMAL_PATH.read_text(encoding="utf-8"))
        main = next(node for node in tree.body if isinstance(node, ast.FunctionDef)
                    and node.name == "main")
        calls = [node for node in ast.walk(main) if isinstance(node, ast.Call)
                 and isinstance(node.func, ast.Attribute) and node.func.attr == "run"
                 and isinstance(node.func.value, ast.Name)
                 and node.func.value.id == "subprocess"]
        formal_runs = [node for node in calls if node.args and isinstance(node.args[0], ast.Name)
                       and node.args[0].id == "argv"]
        self.assertEqual(len(formal_runs), 1)
        validate_line = next(node.lineno for node in ast.walk(main) if isinstance(node, ast.Call)
                             and isinstance(node.func, ast.Name) and node.func.id == "validate_lease")
        self.assertLess(validate_line, formal_runs[0].lineno)
        self.assertIn("formal_invocations\": 1", FORMAL_PATH.read_text(encoding="utf-8"))
        self.assertNotIn("retry", ast.unparse(main).lower())

    def test_launcher_rejects_absent_owner_lease_without_subprocess(self):
        spec = importlib.util.spec_from_file_location("needle_v6_formal_preflight", FORMAL_PATH)
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        with self.assertRaisesRegex(SystemExit, "STOP_NO_EXPLICIT_OWNER_LEASE"):
            module.validate_lease({}, "main", "branch", "default")


if __name__ == "__main__":
    unittest.main(verbosity=2)
