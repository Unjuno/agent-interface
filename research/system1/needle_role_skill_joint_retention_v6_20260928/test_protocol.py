"""Zero-fit construction tests for exact launcher and online-window contracts."""
from pathlib import Path
import tempfile
import unittest
import ast
import hashlib
import importlib.util
import json
import sys
from unittest.mock import patch
from datetime import datetime, timedelta, timezone

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

    def test_rejects_consumption_at_half_open_update_end(self):
        mutated = json.loads(json.dumps(self.record))
        mutated["feedback"][0]["consumed_ns"] = mutated["feedback"][0]["update_end_ns"]
        self.assertIn("update_interval_does_not_cover_consumption",
                      protocol.online_window_errors(mutated)[0])

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

    def test_runner_timestamps_feedback_consumption_at_first_forward(self):
        tree = ast.parse(RUNNER_PATH.read_text(encoding="utf-8"))
        fit = next(node for node in tree.body if isinstance(node, ast.FunctionDef)
                   and node.name == "fit_arm_online")
        assignments = [node for node in ast.walk(fit) if isinstance(node, ast.Assign)
                       and any(isinstance(target, ast.Name) and target.id == "consumed_ns"
                               for target in node.targets)]
        calls = [node for node in assignments if isinstance(node.value, ast.Call)
                 and isinstance(node.value.func, ast.Attribute)
                 and isinstance(node.value.func.value, ast.Name)
                 and node.value.func.value.id == "time"
                 and node.value.func.attr == "perf_counter_ns"]
        self.assertEqual(len(calls), 1)
        forward = next(node for node in ast.walk(fit) if isinstance(node, ast.Call)
                       and isinstance(node.func, ast.Attribute)
                       and isinstance(node.func.value, ast.Name)
                       and node.func.value.id == "F" and node.func.attr == "cross_entropy")
        self.assertLess(calls[0].lineno, forward.lineno)
        self.assertIn("STOP_FEEDBACK_NEVER_CONSUMED", RUNNER_PATH.read_text(encoding="utf-8"))

    def test_auditor_requires_full_receipt_argv_and_independent_lineage(self):
        source = AUDIT_PATH.read_text(encoding="utf-8")
        tree = ast.parse(source)
        self.assertIn("argv != expected_argv", source)
        self.assertIn("expected_docker_argv", source)
        self.assertNotIn("from protocol import", source)
        self.assertNotIn("runner.py\")", source)
        self.assertIn("LEGACY_AUDIT_SHA256", source)
        self.assertTrue(any(isinstance(node, ast.FunctionDef) and node.name == "audit_document"
                            for node in tree.body))

    def test_mounted_source_paths_do_not_assume_repository_parent_tree(self):
        for path in (AUDIT_PATH, FORMAL_PATH):
            source = path.read_text(encoding="utf-8")
            self.assertNotRegex(source, r"(?:HERE|__file__).{0,80}parents\[3\]")

    def test_independent_auditor_rebuilds_argv_and_live_window_contract(self):
        spec = importlib.util.spec_from_file_location("needle_v6_auditor_independence_test", AUDIT_PATH)
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "out"
            output.mkdir()
            self.assertEqual(module.expected_docker_argv(str(HERE), str(output)),
                             protocol.docker_argv(HERE, output))
        positive = {
            "queries": [{"query_id": "q", "worker_id": "inference",
                         "inference_start_ns": 100, "inference_end_ns": 220,
                         "inference_calls": [{"call_start_ns": 110, "call_end_ns": 160}]}],
            "feedback": [{"feedback_id": "f", "query_id": "q", "arrived_ns": 120,
                          "consumed_ns": 145, "update_start_ns": 130, "update_end_ns": 180,
                          "trainer_worker_id": "trainer"}],
        }
        self.assertEqual(module.independent_online_window_errors(positive), [])
        mixed = json.loads(json.dumps(positive))
        mixed["queries"].append({"query_id": "q2", "worker_id": "inference2",
                                 "inference_start_ns": 300, "inference_end_ns": 420,
                                 "inference_calls": [{"call_start_ns": 400, "call_end_ns": 410}]})
        mixed["feedback"].append({"feedback_id": "f2", "query_id": "q2", "arrived_ns": 320,
                                  "consumed_ns": 345, "update_start_ns": 345, "update_end_ns": 390,
                                  "trainer_worker_id": "trainer2"})
        mixed_errors = module.independent_online_window_errors(mixed)
        self.assertIn("update_does_not_overlap_inference_call:f2", mixed_errors)
        self.assertIn("not_every_feedback_update_overlaps_inference", mixed_errors)
        negative = json.loads(json.dumps(positive))
        negative["queries"][0]["inference_calls"] = [{"call_start_ns": 190, "call_end_ns": 210}]
        self.assertTrue(module.independent_online_window_errors(negative))

    def test_independent_online_auditor_rejects_clock_identity_and_interval_mutations(self):
        spec = importlib.util.spec_from_file_location("needle_v6_auditor_mutation_matrix", AUDIT_PATH)
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        valid = {
            "queries": [{"query_id": "q", "worker_id": "inference",
                         "inference_start_ns": 100, "inference_end_ns": 220,
                         "inference_calls": [{"call_start_ns": 110, "call_end_ns": 160}]}],
            "feedback": [{"feedback_id": "f", "query_id": "q", "arrived_ns": 120,
                          "consumed_ns": 145, "update_start_ns": 130, "update_end_ns": 180,
                          "trainer_worker_id": "trainer"}],
        }
        mutations = {
            "boolean_arrival_clock": lambda r: r["feedback"][0].update(arrived_ns=True),
            "arrival_after_query_end": lambda r: r["feedback"][0].update(arrived_ns=221),
            "consumed_before_arrival": lambda r: r["feedback"][0].update(consumed_ns=119),
            "update_reversed": lambda r: r["feedback"][0].update(update_start_ns=180, update_end_ns=130),
            "consumption_outside_update": lambda r: r["feedback"][0].update(consumed_ns=125),
            "consumption_at_update_end": lambda r: r["feedback"][0].update(consumed_ns=180),
            "same_worker_identity": lambda r: r["feedback"][0].update(trainer_worker_id="inference"),
            "query_call_outside_window": lambda r: r["queries"][0].update(inference_calls=[{"call_start_ns": 90, "call_end_ns": 120}]),
            "duplicate_feedback_id": lambda r: r["feedback"].append(dict(r["feedback"][0])),
            "duplicate_query_id": lambda r: r["queries"].append(dict(r["queries"][0])),
            "nonoverlapping_second_event": lambda r: (r["queries"].append({"query_id": "q2", "worker_id": "i2", "inference_start_ns": 300, "inference_end_ns": 420, "inference_calls": [{"call_start_ns": 400, "call_end_ns": 410}]}), r["feedback"].append({"feedback_id": "f2", "query_id": "q2", "arrived_ns": 320, "consumed_ns": 345, "update_start_ns": 345, "update_end_ns": 390, "trainer_worker_id": "t2"})),
        }
        for name, mutate in mutations.items():
            with self.subTest(name=name):
                candidate = json.loads(json.dumps(valid))
                mutate(candidate)
                self.assertTrue(module.independent_online_window_errors(candidate), name)

    def test_independent_auditor_holds_when_formal_receipt_is_absent(self):
        spec = importlib.util.spec_from_file_location("needle_v6_missing_receipt_test", AUDIT_PATH)
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        result = module.audit_document({"runs": []}, receipt=None)
        self.assertEqual(result["decision"], "HOLD_AUDIT_INTEGRITY")
        self.assertIn("formal_receipt_missing", result["errors"])

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
        docker_context_line = next(node.lineno for node in calls
                                   if node.args and isinstance(node.args[0], ast.List)
                                   and any(isinstance(item, ast.Constant) and item.value == "docker"
                                           for item in node.args[0].elts))
        self.assertLess(validate_line, docker_context_line)
        self.assertIn("formal_invocations\": 1", FORMAL_PATH.read_text(encoding="utf-8"))
        self.assertNotIn("retry", ast.unparse(main).lower())

    def test_launcher_rejects_absent_owner_lease_without_subprocess(self):
        spec = importlib.util.spec_from_file_location("needle_v6_formal_preflight", FORMAL_PATH)
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        with self.assertRaisesRegex(SystemExit, "STOP_NO_EXPLICIT_OWNER_LEASE"):
            module.validate_lease({}, "main", "branch", "default")

    def test_launcher_requires_live_owner_comment_payload_exactly_bound_to_lease(self):
        spec = importlib.util.spec_from_file_location("needle_v6_owner_comment_test", FORMAL_PATH)
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        now = datetime.now(timezone.utc)
        start = (now - timedelta(minutes=1)).isoformat()
        end = (now + timedelta(minutes=10)).isoformat()
        expiry = end
        lease = {"schema": module.LEASE_SCHEMA, "allocation": module.ALLOCATION,
                 "issue": module.ISSUE, "main_sha": "a" * 40, "branch": "branch",
                 "docker_context": "desktop-linux", "lease_id": "slot-123",
                 "slot_start_utc": start, "slot_end_utc": end, "expires_at_utc": expiry,
                 "owner_comment_url": "https://github.com/Unjuno/agent-interface/issues/5085#issuecomment-12345"}
        payload = {key: lease[key] for key in ("schema", "allocation", "issue", "main_sha",
                  "branch", "docker_context", "lease_id", "slot_start_utc", "slot_end_utc",
                  "expires_at_utc")}
        body = "<!-- needle-docker-owner-lease-v1\n" + json.dumps(payload) + "\n-->"
        record = {"html_url": lease["owner_comment_url"],
                  "issue_url": "https://api.github.com/repos/Unjuno/agent-interface/issues/5085",
                  "user": {"login": "Unjuno"}, "body": body}
        verified = module.validate_lease(lease, "a" * 40, "branch", "desktop-linux", record)
        self.assertEqual(verified["user_login"], "Unjuno")
        forged = dict(record, body=body.replace("slot-123", "forged"))
        with self.assertRaisesRegex(SystemExit, "STOP_LEASE_OWNER_COMMENT_PAYLOAD_MISMATCH"):
            module.validate_lease(lease, "a" * 40, "branch", "desktop-linux", forged)
        wrong_owner = dict(record, user={"login": "attacker"})
        with self.assertRaisesRegex(SystemExit, "STOP_LEASE_OWNER_COMMENT_AUTHOR"):
            module.validate_lease(lease, "a" * 40, "branch", "desktop-linux", wrong_owner)

    def test_launcher_rechecks_owner_window_at_docker_boundaries(self):
        spec = importlib.util.spec_from_file_location("needle_v6_lease_window_test", FORMAL_PATH)
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        start = datetime(2026, 9, 28, 12, tzinfo=timezone.utc)
        lease = {"slot_start_utc": start.isoformat(),
                 "slot_end_utc": (start + timedelta(minutes=10)).isoformat(),
                 "expires_at_utc": (start + timedelta(minutes=5)).isoformat()}
        self.assertTrue(module.lease_window_active(lease, start + timedelta(minutes=4)))
        self.assertFalse(module.lease_window_active(lease, start + timedelta(minutes=5)))
        self.assertFalse(module.lease_window_active(lease, start - timedelta(seconds=1)))
        source = FORMAL_PATH.read_text(encoding="utf-8")
        self.assertIn("LEASE_SLOT_EXPIRED_BEFORE_DOCKER", source)
        self.assertIn("LEASE_SLOT_EXPIRED_BEFORE_DOCKER_RUN", source)

    def test_independent_audit_binds_owner_url_and_rejects_duplicate_payload_keys(self):
        spec = importlib.util.spec_from_file_location("needle_v6_owner_audit_test", AUDIT_PATH)
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        expected = {
            "schema": "needle-docker-owner-lease-v1",
            "allocation": protocol.ALLOCATION, "issue": 5085,
            "main_sha": "a" * 40, "branch": "branch", "docker_context": "desktop-linux",
            "lease_id": "slot-123", "slot_start_utc": "2026-09-28T12:00:00+00:00",
            "slot_end_utc": "2026-09-28T12:10:00+00:00",
            "expires_at_utc": "2026-09-28T12:05:00+00:00",
        }
        receipt = {"owner_comment_url": "https://github.com/Unjuno/agent-interface/issues/5085#issuecomment-12345",
                   "main_sha": expected["main_sha"], "branch": expected["branch"],
                   "docker_context": expected["docker_context"], "lease_id": expected["lease_id"],
                   "slot_start_utc": expected["slot_start_utc"], "slot_end_utc": expected["slot_end_utc"],
                   "expires_at_utc": expected["expires_at_utc"]}
        comment = {"html_url": receipt["owner_comment_url"],
                   "issue_url": "https://api.github.com/repos/Unjuno/agent-interface/issues/5085",
                   "user_login": "Unjuno",
                   "body": "<!-- needle-docker-owner-lease-v1\n" + json.dumps(expected)
                           + "\n-->"}
        with patch.object(module, "fetch_owner_comment_record", return_value={
                "html_url": comment["html_url"], "issue_url": comment["issue_url"],
                "user": {"login": "Unjuno"}, "body": comment["body"]}):
            valid_errors = module.audit_document(
                {"runs": []}, {**receipt, "owner_lease_comment": comment})["errors"]
        self.assertNotIn("formal_owner_comment_payload", valid_errors)
        self.assertNotIn("formal_owner_comment_live_record", valid_errors)
        fake_receipt = {**receipt, "owner_comment_url": "https://example.invalid/fake",
                        "owner_lease_comment": dict(comment, html_url="https://example.invalid/fake")}
        self.assertIn("formal_owner_comment_payload",
                      module.audit_document({"runs": []}, fake_receipt)["errors"])
        duplicate = json.dumps(expected)[:-1] + ',"lease_id":"attacker","lease_id":"slot-123"}'
        duplicate_comment = dict(comment, body="<!-- needle-docker-owner-lease-v1\n" + duplicate + "\n-->")
        with patch.object(module, "fetch_owner_comment_record", return_value={
                "html_url": comment["html_url"], "issue_url": comment["issue_url"],
                "user": {"login": "Unjuno"}, "body": duplicate_comment["body"]}):
            self.assertIn("formal_owner_comment_payload", module.audit_document(
                {"runs": []}, {**receipt, "owner_lease_comment": duplicate_comment})["errors"])
        forged_receipt = {**receipt, "owner_lease_comment": comment}
        with patch.object(module, "fetch_owner_comment_record", return_value=None):
            self.assertIn("formal_owner_comment_live_record",
                          module.audit_document({"runs": []}, forged_receipt)["errors"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
