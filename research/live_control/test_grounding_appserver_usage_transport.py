"""Compose the real JSONL client with grounding and the adaptive attempt ledger."""
import json
import hashlib
import importlib.util
import os
from pathlib import Path
import sys
import tempfile
import unittest

from research.live_control import adaptive_acquisition_caller_v3 as caller
from research.live_control.codex_app_server_client_v2 import CodexAppServerClient
from research.live_control.integrated_efficiency_app_server_model_v1 import (
    PersistentGroundingModel,
)
from research.live_control.v3_persistent_grounding_adapter_v1 import (
    V3PersistentGroundingAdapter,
)
from research.live_control.issue57_v3_attempt_ledger_v1 import (
    AppendOnlyAttemptLedger, make_row,
)
from research.live_control.issue57_v3_trace_adapter_v1 import project_task
from research.live_control.calc_durable_allocation_v1 import (
    DurableCalcAllocation, audit_allocation,
)


PEER = r'''
import json, sys

def send(value):
    sys.stdout.write(json.dumps(value, separators=(",", ":")) + "\n")
    sys.stdout.flush()

for line in sys.stdin:
    request = json.loads(line)
    method = request.get("method")
    if method == "initialized":
        continue
    if method == "initialize":
        send({"id": request["id"], "result": {}})
    elif method == "thread/start":
        send({"id": request["id"], "result": {"thread": {"id": "thread-ledger-1"}}})
    elif method == "turn/start":
        send({"id": request["id"], "result": {"turn": {"id": "turn-ledger-1"}}})
        send({"method": "thread/tokenUsage/updated", "params": {
            "threadId": "thread-ledger-1", "turnId": "turn-ledger-1",
            "tokenUsage": {"last": {"inputTokens": 1234,
                "cachedInputTokens": 234, "cacheWriteInputTokens": 0,
                "outputTokens": 56, "reasoningOutputTokens": 12}}}})
        send({"method": "turn/completed", "params": {
            "threadId": "thread-ledger-1", "turn": {
                "id": "turn-ledger-1", "status": "completed",
                "items": [{"type": "agentMessage", "text": "{}"}]}}})
    else:
        send({"id": request.get("id"), "error": {"code": -32000,
            "message": "unexpected fixture method: " + str(method)}})
'''


class GroundingAppServerUsageTransportTest(unittest.TestCase):
    @unittest.skipIf(os.name == "nt" and sys.version_info[:2] < (3, 12),
                     "app-server pipe transport requires Windows Python 3.12+")
    def test_thread_and_turn_identity_with_usage_reach_failed_attempt_ledger(self):
        with tempfile.TemporaryDirectory(prefix="grounding-appserver-ledger-") as tmp:
            root = Path(tmp)
            workspace = root / "workspace"
            workspace.mkdir()
            image = root / "observation.fixture"
            image.write_bytes(b"synthetic app-server composition fixture")
            journal_path = root / "protocol.jsonl"
            client = CodexAppServerClient(
                [sys.executable, "-B", "-c", PEER],
                cwd=str(workspace), journal_path=str(journal_path))
            model = None
            try:
                client.initialize()
                model = PersistentGroundingModel(
                    root / "session", workspace, node="unused", cli="unused",
                    client=client, path_converter=str,
                    model="synthetic-model", effort="medium")
                v3_model = V3PersistentGroundingAdapter(model)
                events = []
                execute_calls = []

                def anchor(_payload):
                    return v3_model(root / "call", "synthetic request", image,
                                    "compiled", workspace)

                result = caller.run({
                    "target": "synthetic form", "route": "cold",
                    "coarse_origin": "caller_provided",
                    "provided_coarse": {"status": "candidate"},
                    "cached_target": None, "local_repair_on": [], "repair_on": [],
                    "session_id": "synthetic-appserver-session"},
                    {"observe_source": lambda _payload: {},
                     "acquire_anchor": lambda _payload: {},
                     "anchor_model": anchor,
                     "final_revalidate": lambda _payload: {"status": "revalidated"},
                     "execute": lambda payload: execute_calls.append(payload) or
                         {"status": "completed"},
                     "verify_effect": lambda _payload: {"status": "unavailable"},
                     "journal": events.append})

                attempt, = result["attempt_ledger"]
                comparison_row = make_row("provider-failure-arm-task-01", result,
                    {"status": "unavailable", "verified": False,
                     "keys_down": None, "buttons_down": None,
                     "evidence_ref": None, "evidence_digest": None},
                    {"status": "unavailable", "evidence_ref": None,
                     "evidence_digest": None})
                ledger = AppendOnlyAttemptLedger(
                    root / "issue57-attempts.jsonl",
                    ["provider-failure-arm-task-01"])
                ledger.append(comparison_row)
                ledger_audit = ledger.audit()
                self.assertEqual(ledger_audit["rows"], 1)
                self.assertEqual(ledger_audit["attempts"], 1)
                self.assertIsNone(comparison_row["task_effect"])
                self.assertEqual(result["outcome"], "CALLER_FAILED")
                self.assertEqual(result["accounting"]["attempted_calls"], 1)
                self.assertEqual(result["accounting"]["completed_calls"], 0)
                self.assertEqual(attempt["call_id"], "turn-ledger-1")
                self.assertEqual(attempt["thread_id"], "thread-ledger-1")
                self.assertEqual(attempt["requested_model"], "synthetic-model")
                self.assertEqual(attempt["requested_effort"], "medium")
                self.assertEqual(attempt["usage"], {
                    "input_tokens": 1234, "cached_input_tokens": 234,
                    "cache_write_input_tokens": 0, "output_tokens": 56,
                    "reasoning_output_tokens": 12})
                failure_receipt = json.loads(
                    (root / "call" / "failure.json").read_text(encoding="utf-8"))
                self.assertEqual(failure_receipt["requested_model"],
                                 attempt["requested_model"])
                self.assertEqual(failure_receipt["requested_effort"],
                                 attempt["requested_effort"])
                self.assertEqual(result["accounting"]["usage_totals"]["input_tokens"], 1234)
                projected = project_task("plain", 0, result,
                    {"submission_count": 0, "exact_submission": False},
                    {"local_observations": 1, "durable_calls": 1,
                     "pointer_admissions": 0, "old_target_pointer_admissions": 0,
                     "releases_verified": False, "elapsed_ns": 1,
                     "source_to_completion_ns": None, "input_feedback_ns": [],
                     "repair": {"required": False, "old_reference_status": None,
                         "old_reference_pointer_admissions": 0,
                         "attempted": False, "succeeded": False}})
                self.assertEqual(projected["status"], "HOLD")
                self.assertEqual(projected["reason"],
                    "failed_attempt_not_representable_in_v1")
                self.assertEqual(projected["caller_result"], result)
                self.assertEqual(execute_calls, [])
                self.assertIsNone(result["task_effect"])
                self.assertIsNone(result["accounting"]["cost"])
                protocol = [json.loads(line) for line in
                            journal_path.read_text(encoding="utf-8").splitlines()]
                usage_events = [row["message"] for row in protocol
                                if row["direction"] == "received" and
                                row["message"].get("method") == "thread/tokenUsage/updated"]
                self.assertEqual(len(usage_events), 1)
                self.assertEqual(usage_events[0]["params"]["threadId"], attempt["thread_id"])
                self.assertEqual(usage_events[0]["params"]["turnId"], attempt["call_id"])
                sent = [row["message"] for row in protocol
                        if row["direction"] == "sent"]
                thread_start, = [row for row in sent if row["method"] == "thread/start"]
                turn_start, = [row for row in sent if row["method"] == "turn/start"]
                self.assertEqual(thread_start["params"]["model"],
                                 attempt["requested_model"])
                self.assertEqual(turn_start["params"]["effort"],
                                 attempt["requested_effort"])
                self.assertTrue(any(event.get("event") == "model_attempt_finished" and
                                    event.get("thread_id") == attempt["thread_id"]
                                    for event in events))
            finally:
                if model is not None:
                    model.close()
                client.close(timeout=2)

    @unittest.skipIf(os.name == "nt" and sys.version_info[:2] < (3, 12),
                     "app-server pipe transport requires Windows Python 3.12+")
    @unittest.skipUnless(importlib.util.find_spec("PIL") is not None,
                         "Calc guarded adapter import requires Pillow")
    def test_provider_transport_failure_is_retained_in_durable_g10_allocation(self):
        from research.live_control.calc_g10_caller_v1 import run_g10_in_durable_allocation

        with tempfile.TemporaryDirectory(prefix="grounding-durable-allocation-") as tmp:
            root = Path(tmp)
            workspace = root / "workspace"
            workspace.mkdir()
            image = root / "observation.fixture"
            image.write_bytes(b"synthetic durable app-server composition fixture")
            client = CodexAppServerClient(
                [sys.executable, "-B", "-c", PEER], cwd=str(workspace),
                journal_path=str(root / "protocol.jsonl"))
            model = None
            try:
                client.initialize()
                model = PersistentGroundingModel(
                    root / "session", workspace, node="unused", cli="unused",
                    client=client, path_converter=str,
                    model="synthetic-model", effort="medium")
                provider = V3PersistentGroundingAdapter(model)
                conditions = {"model": "synthetic-model", "effort": "medium",
                              "task": "two-cell-save", "route": "cold"}
                allocation_root = root / "allocations"
                allocation_root.mkdir()
                ledger = DurableCalcAllocation(
                    allocation_root, "attempt-provider-join-01",
                    source_sha256=hashlib.sha256(b"frozen task source").hexdigest(),
                    observation_ids=["observation-01"],
                    source_hashes={"caller.py": hashlib.sha256(
                        b"frozen caller source").hexdigest()},
                    conditions=conditions)
                journal = []
                adapters = {
                    "observe_source": lambda _payload: {"sequence": 1},
                    "acquire_anchor": lambda _payload: {"image": str(image)},
                    "anchor_model": lambda _payload: provider(
                        root / "provider-call", "synthetic grounding request", image,
                        "compiled", workspace),
                    "verify_effect": lambda _payload: {"status": "unavailable"},
                    "journal": journal.append,
                }
                spec = {
                    "target": "synthetic Calc task", "route": "cold",
                    "coarse_origin": "caller_provided",
                    "provided_coarse": {"status": "candidate"},
                    "cached_target": None, "local_repair_on": [],
                    "repair_on": [], "session_id": "durable-provider-fixture",
                }
                result = run_g10_in_durable_allocation(
                    spec, adapters, lambda _payload: {"interface_id": "unused"},
                    None, {}, ledger,
                    perceive=lambda *_args: {}, verify_effect=lambda *_args: {},
                    proposal_worker=object(), cancelled=lambda: False)

                receipt = audit_allocation(ledger.path)
                self.assertEqual(result["outcome"], "CALLER_FAILED")
                self.assertEqual(receipt["status"], "audited")
                self.assertEqual(receipt["outcome"], "CALLER_FAILED")
                self.assertFalse(receipt["receipt_persisted"])
                self.assertFalse(receipt["effect_receipt_persisted"])
                attempt, = receipt["attempt_ledger"]
                self.assertEqual(attempt["status"], "failed")
                self.assertEqual(attempt["call_id"], "turn-ledger-1")
                self.assertEqual(attempt["thread_id"], "thread-ledger-1")
                self.assertEqual(attempt["requested_model"], "synthetic-model")
                self.assertEqual(attempt["requested_effort"], "medium")
                self.assertEqual(attempt["usage"], {
                    "input_tokens": 1234, "cached_input_tokens": 234,
                    "cache_write_input_tokens": 0, "output_tokens": 56,
                    "reasoning_output_tokens": 12})
                self.assertEqual(receipt["accounting"]["usage_totals"]["input_tokens"], 1234)
                self.assertTrue(any(event.get("event") == "model_attempt_finished" and
                                    event.get("call_id") == "turn-ledger-1"
                                    for event in journal))
                protocol = [json.loads(line) for line in
                    (root / "protocol.jsonl").read_text(encoding="utf-8").splitlines()]
                self.assertTrue(any(row["direction"] == "received" and
                    row["message"].get("method") == "thread/tokenUsage/updated" and
                    row["message"]["params"].get("turnId") == attempt["call_id"]
                    for row in protocol))
            finally:
                if model is not None:
                    model.close()
                client.close(timeout=2)

    @unittest.skipIf(os.name == "nt" and sys.version_info[:2] < (3, 12),
                     "app-server pipe transport requires Windows Python 3.12+")
    @unittest.skipUnless(importlib.util.find_spec("PIL") is not None,
                         "Calc guarded adapter import requires Pillow")
    def test_provider_failure_usage_joins_prospective_task_custody(self):
        from datetime import datetime, timedelta, timezone
        from research.live_control.calc_g10_caller_v1 import run_g10_in_durable_allocation
        from research.live_control.integrated_efficiency_protocol_v1 import ARMS, TASKS
        from research.live_control.issue57_v3_prospective_run_v1 import ProspectiveRun

        with tempfile.TemporaryDirectory(prefix="grounding-prospective-custody-") as tmp:
            root = Path(tmp)
            workspace = root / "workspace"
            workspace.mkdir()
            image = root / "observation.fixture"
            image.write_bytes(b"synthetic prospective composition fixture")
            allocation_path = root / "allocation.json"
            allocation = {
                "allocation_id": "synthetic-prospective-join-01",
                "host_id": "synthetic-local-host", "owner": "offline-test",
                "exclusive": True,
                "expires_at_utc": (datetime.now(timezone.utc) +
                    timedelta(hours=1)).isoformat(),
                "task_ids": list(TASKS), "arms": list(ARMS),
                "model": "synthetic-model",
                "settings": {"effort": "medium", "provider": "fake"},
                "order_seed": 57,
            }
            allocation_path.write_text(json.dumps(allocation), encoding="utf-8")
            source_root = Path(__file__).resolve().parents[2]
            run = ProspectiveRun(allocation_path, root / "prospective-run",
                source_root=source_root, allocation_verifier=lambda *_args: True)
            task_source = hashlib.sha256(b"synthetic frozen task source").hexdigest()
            ledger = run.create_task_custodian("plain", 0,
                source_sha256=task_source, observation_ids=["observation-prospective-01"],
                conditions={"fixture": "synthetic-provider-failure"})

            client = CodexAppServerClient(
                [sys.executable, "-B", "-c", PEER], cwd=str(workspace),
                journal_path=str(root / "protocol.jsonl"))
            model = None
            try:
                client.initialize()
                model = PersistentGroundingModel(
                    root / "session", workspace, node="unused", cli="unused",
                    client=client, path_converter=str,
                    model="synthetic-model", effort="medium")
                provider = V3PersistentGroundingAdapter(model)
                conditions = {"model": "synthetic-model", "effort": "medium",
                              "task": "two-cell-save", "route": "cold"}
                journal = []
                adapters = {
                    "observe_source": lambda _payload: {"sequence": 1},
                    "acquire_anchor": lambda _payload: {"image": str(image)},
                    "anchor_model": lambda _payload: provider(
                        root / "provider-call", "synthetic grounding request", image,
                        "compiled", workspace),
                    "verify_effect": lambda _payload: {"status": "unavailable"},
                    "journal": journal.append,
                }
                spec = {
                    "target": "synthetic Calc task", "route": "cold",
                    "coarse_origin": "caller_provided",
                    "provided_coarse": {"status": "candidate"},
                    "cached_target": None, "local_repair_on": [],
                    "repair_on": [], "session_id": "prospective-provider-fixture",
                }
                result = run_g10_in_durable_allocation(
                    spec, adapters, lambda _payload: {"interface_id": "unused"},
                    None, {}, ledger,
                    perceive=lambda *_args: {}, verify_effect=lambda *_args: {},
                    proposal_worker=object(), cancelled=lambda: False)
                telemetry = {
                    "local_observations": 1, "durable_calls": 1,
                    "pointer_admissions": 0, "old_target_pointer_admissions": 0,
                    "releases_verified": False, "elapsed_ns": 1,
                    "source_to_completion_ns": None, "input_feedback_ns": [],
                    "repair": {"required": False, "old_reference_status": None,
                        "old_reference_pointer_admissions": 0,
                        "attempted": False, "succeeded": False},
                }
                projected = run.record_task("plain", 0, result,
                    {"submission_count": 0, "exact_submission": False}, telemetry,
                    custodian_path=ledger.path)
                task_event, = [json.loads(line) for line in
                    (root / "prospective-run" / "lifecycle.jsonl").read_text(
                        encoding="utf-8").splitlines()
                    if json.loads(line)["event"] == "task"]
                custody = task_event["payload"]["custody"]
                audit = custody["audit"]
                self.assertEqual(result["outcome"], "CALLER_FAILED")
                self.assertEqual(custody["status"], "audited")
                self.assertEqual(audit["status"], "audited")
                self.assertEqual(audit["attempt_ledger"][0]["call_id"],
                                 "turn-ledger-1")
                self.assertEqual(audit["attempt_ledger"][0]["usage"]["input_tokens"],
                                 1234)
                self.assertEqual(projected["status"], "HOLD")
                self.assertEqual(projected["reason"],
                                 "failed_attempt_not_representable_in_v1")
                finished = run.finish([])
                self.assertEqual(finished["status"], "HOLD")
                self.assertEqual(len(finished["missing_assignments"]), 17)
                self.assertFalse(json.loads((root / "prospective-run" /
                    "run-manifest.json").read_text(encoding="utf-8"))["dispatch_enabled"])
            finally:
                if model is not None:
                    model.close()
                client.close(timeout=2)

    @unittest.skipUnless(importlib.util.find_spec("PIL") is not None,
                         "Calc guarded adapter import requires Pillow")
    def test_unknown_usage_and_deferred_attempts_reach_prospective_custody(self):
        from datetime import datetime, timedelta, timezone
        from research.live_control.adaptive_acquisition_caller_v3 import ModelFailure
        from research.live_control.calc_g10_caller_v1 import run_g10_in_durable_allocation
        from research.live_control.integrated_efficiency_protocol_v1 import ARMS, TASKS
        from research.live_control.issue57_v3_prospective_run_v1 import ProspectiveRun

        usage = {"input_tokens": 7, "cached_input_tokens": 1,
                 "cache_write_input_tokens": 0, "output_tokens": 3,
                 "reasoning_output_tokens": 1}
        cases = [
            ("unknown-usage", "CALLER_FAILED", "FAILED_UPSTREAM", None),
            ("deferred-known-usage", "TASK_DEFERRED", "DEFERRED_UPSTREAM", usage),
        ]
        for case_name, expected_outcome, typed_status, case_usage in cases:
            with self.subTest(case=case_name), tempfile.TemporaryDirectory(
                    prefix="prospective-" + case_name + "-") as tmp:
                root = Path(tmp)
                workspace = root / "workspace"
                workspace.mkdir()
                image = root / "observation.fixture"
                image.write_bytes(b"synthetic custody case " + case_name.encode())
                allocation_path = root / "allocation.json"
                allocation = {
                    "allocation_id": "synthetic-" + case_name,
                    "host_id": "synthetic-local-host", "owner": "offline-test",
                    "exclusive": True,
                    "expires_at_utc": (datetime.now(timezone.utc) +
                        timedelta(hours=1)).isoformat(),
                    "task_ids": list(TASKS), "arms": list(ARMS),
                    "model": "synthetic-model",
                    "settings": {"effort": "medium", "provider": "fake"},
                    "order_seed": 57,
                }
                allocation_path.write_text(json.dumps(allocation), encoding="utf-8")
                source_root = Path(__file__).resolve().parents[2]
                run = ProspectiveRun(allocation_path, root / "prospective-run",
                    source_root=source_root, allocation_verifier=lambda *_args: True)
                task_source = hashlib.sha256(case_name.encode()).hexdigest()
                ledger = run.create_task_custodian("plain", 0,
                    source_sha256=task_source,
                    observation_ids=["observation-" + case_name],
                    conditions={"fixture": case_name})

                def fail_provider(_payload):
                    raise ModelFailure("synthetic " + case_name,
                        call_id="turn-" + case_name,
                        thread_id="thread-" + case_name,
                        usage=case_usage, requested_model="synthetic-model",
                        requested_effort="medium", visible_images_submitted=1,
                        wait_ns=3, typed_status=typed_status)

                journal = []
                adapters = {
                    "observe_source": lambda _payload: {"sequence": 1},
                    "acquire_anchor": lambda _payload: {"image": str(image)},
                    "anchor_model": fail_provider,
                    "verify_effect": lambda _payload: {"status": "unavailable"},
                    "journal": journal.append,
                }
                spec = {
                    "target": "synthetic Calc task", "route": "cold",
                    "coarse_origin": "caller_provided",
                    "provided_coarse": {"status": "candidate"},
                    "cached_target": None, "local_repair_on": [],
                    "repair_on": [], "session_id": "prospective-" + case_name,
                }
                result = run_g10_in_durable_allocation(
                    spec, adapters, lambda _payload: {"interface_id": "unused"},
                    None, {}, ledger,
                    perceive=lambda *_args: {}, verify_effect=lambda *_args: {},
                    proposal_worker=object(), cancelled=lambda: False)
                self.assertEqual(result["outcome"], expected_outcome, result)
                self.assertEqual(result["attempt_ledger"][0]["usage"], case_usage)
                projected = run.record_task("plain", 0, result,
                    {"submission_count": 0, "exact_submission": False}, {
                        "local_observations": 1, "durable_calls": 1,
                        "pointer_admissions": 0,
                        "old_target_pointer_admissions": 0,
                        "releases_verified": False, "elapsed_ns": 1,
                        "source_to_completion_ns": None, "input_feedback_ns": [],
                        "repair": {"required": False,
                            "old_reference_status": None,
                            "old_reference_pointer_admissions": 0,
                            "attempted": False, "succeeded": False},
                    }, custodian_path=ledger.path)
                task_event, = [json.loads(line) for line in
                    (root / "prospective-run" / "lifecycle.jsonl").read_text(
                        encoding="utf-8").splitlines()
                    if json.loads(line)["event"] == "task"]
                self.assertEqual(task_event["payload"]["custody"]["status"],
                                 "audited")
                self.assertEqual(projected["status"], "HOLD")
                self.assertEqual(projected["reason"],
                                 "failed_attempt_not_representable_in_v1")
                self.assertEqual(run.finish([])["status"], "HOLD")

    @unittest.skipUnless(importlib.util.find_spec("PIL") is not None,
                         "Calc guarded adapter import requires Pillow")
    def test_jsonl_provider_success_joins_durable_prospective_custody(self):
        from datetime import datetime, timedelta, timezone
        from unittest.mock import patch
        from research.live_control.calc_g10_caller_v1 import run_g10_in_durable_allocation
        from research.live_control.integrated_efficiency_protocol_v1 import ARMS, TASKS
        from research.live_control.issue57_v3_prospective_run_v1 import ProspectiveRun

        with tempfile.TemporaryDirectory(prefix="prospective-jsonl-success-") as tmp:
            root = Path(tmp)
            workspace = root / "workspace"
            workspace.mkdir()
            image = root / "observation.fixture"
            image.write_bytes(b"synthetic JSONL success observation")
            answer = {
                "format": "compiled-form-grounding-v1",
                "field": {"point_space": "source_observation_pixels",
                          "point": {"x": 10, "y": 20},
                          "motion_model": "surface_origin_translation"},
                "submit": {"point_space": "source_observation_pixels",
                           "point": {"x": 30, "y": 40},
                           "motion_model": "surface_origin_translation"},
                "method": {"first_action": "enter_exact_token",
                           "continue_when": "field_pixels_changed_and_submit_revalidated",
                           "second_action": "activate_submit",
                           "complete_when": "submission_pixels_changed_then_independent_score"},
            }
            success_peer = PEER.replace('"text": "{}"',
                                        '"text": ' + json.dumps(json.dumps(answer)))
            allocation_path = root / "allocation.json"
            allocation = {
                "allocation_id": "synthetic-prospective-jsonl-success-01",
                "host_id": "synthetic-local-host", "owner": "offline-test",
                "exclusive": True,
                "expires_at_utc": (datetime.now(timezone.utc) +
                    timedelta(hours=1)).isoformat(),
                "task_ids": list(TASKS), "arms": list(ARMS),
                "model": "synthetic-model",
                "settings": {"effort": "medium", "provider": "fake"},
                "order_seed": 57,
            }
            allocation_path.write_text(json.dumps(allocation), encoding="utf-8")
            source_root = Path(__file__).resolve().parents[2]
            run = ProspectiveRun(allocation_path, root / "prospective-run",
                source_root=source_root, allocation_verifier=lambda *_args: True)
            ledger = run.create_task_custodian("plain", 0,
                source_sha256=hashlib.sha256(b"synthetic JSONL success source").hexdigest(),
                observation_ids=["observation-jsonl-success-01"],
                conditions={"fixture": "synthetic-jsonl-provider-success"})
            protocol_path = root / "protocol.jsonl"
            client = CodexAppServerClient(
                [sys.executable, "-B", "-c", success_peer], cwd=str(workspace),
                journal_path=str(protocol_path))
            model = None
            try:
                client.initialize()
                model = PersistentGroundingModel(
                    root / "session", workspace, node="unused", cli="unused",
                    client=client, path_converter=str,
                    model="synthetic-model", effort="medium")
                provider = V3PersistentGroundingAdapter(model)
                usage = {"input_tokens": 1234, "cached_input_tokens": 234,
                         "cache_write_input_tokens": 0, "output_tokens": 56,
                         "reasoning_output_tokens": 12}
                adapters = {
                    "observe_source": lambda _payload: {"sequence": 1},
                    "acquire_anchor": lambda _payload: {"image": str(image)},
                    "anchor_model": lambda _payload: provider(
                        root / "provider-call", "synthetic grounding request", image,
                        "compiled", workspace),
                    "final_revalidate": lambda _payload: {"status": "revalidated"},
                    "verify_effect": lambda _payload: {
                        "status": "succeeded", "evidence_ref": "fixture://saved-cell",
                        "evidence_digest": "b" * 64, "effect_scope": "cell-A1 value"},
                }
                spec = {
                    "target": "synthetic Calc save", "route": "cold",
                    "coarse_origin": "caller_provided",
                    "provided_coarse": {"status": "candidate"},
                    "cached_target": None, "local_repair_on": [], "repair_on": [],
                    "session_id": "prospective-jsonl-success-01",
                }
                execution = {"outcome": "TASK_SUCCEEDED", "completed_transitions": 2,
                             "critical_events": [{"event": "action_terminal",
                                                  "input_dispatched": True}]}
                with patch("research.live_control.calc_g10_caller_v1.run_with_bounded_fresh_proposal",
                           return_value=execution):
                    result = run_g10_in_durable_allocation(
                        spec, adapters,
                        lambda _payload: {"interface_id": "synthetic-calc-interface"},
                        object(), {}, ledger,
                        perceive=lambda *_args: {}, verify_effect=lambda *_args: {},
                        proposal_worker=object(), cancelled=lambda: False)
                telemetry = {
                    "local_observations": 2, "durable_calls": 1,
                    "pointer_admissions": 0, "old_target_pointer_admissions": 0,
                    "releases_verified": True, "elapsed_ns": 100,
                    "source_to_completion_ns": 80, "input_feedback_ns": [],
                    "repair": {"required": False, "old_reference_status": None,
                        "old_reference_pointer_admissions": 0,
                        "attempted": False, "succeeded": False},
                }
                projected = run.record_task("plain", 0, result,
                    {"submission_count": 1, "exact_submission": True}, telemetry,
                    custodian_path=ledger.path)
                lifecycle = [json.loads(line) for line in
                    (root / "prospective-run" / "lifecycle.jsonl").read_text(
                        encoding="utf-8").splitlines()]
                task_event, = [row for row in lifecycle if row["event"] == "task"]
                audit = task_event["payload"]["custody"]["audit"]
                protocol = [json.loads(line) for line in
                    protocol_path.read_text(encoding="utf-8").splitlines()]
                usage_event, = [row["message"] for row in protocol
                    if row["direction"] == "received" and
                    row["message"].get("method") == "thread/tokenUsage/updated"]
                self.assertEqual(result["outcome"], "TASK_SUCCEEDED")
                self.assertEqual(result["attempt_ledger"][0]["status"], "completed")
                self.assertEqual(result["attempt_ledger"][0]["call_id"], "turn-ledger-1")
                self.assertEqual(result["attempt_ledger"][0]["thread_id"], "thread-ledger-1")
                self.assertEqual(result["attempt_ledger"][0]["usage"], usage)
                self.assertEqual(result["accounting"]["usage_totals"], usage)
                self.assertEqual(usage_event["params"]["turnId"], "turn-ledger-1")
                self.assertEqual(usage_event["params"]["tokenUsage"]["last"]["inputTokens"], 1234)
                self.assertEqual(projected["status"], "projected")
                self.assertEqual(audit["status"], "audited")
                self.assertTrue(audit["receipt_persisted"])
                self.assertTrue(audit["effect_receipt_persisted"])
                self.assertEqual(audit["attempt_ledger"][0]["usage"], usage)
                finished = run.finish([])
                self.assertEqual(finished["status"], "HOLD")
                self.assertEqual(len(finished["missing_assignments"]), 17)
                self.assertFalse(json.loads((root / "prospective-run" /
                    "run-manifest.json").read_text(encoding="utf-8"))["dispatch_enabled"])
            finally:
                if model is not None:
                    model.close()
                client.close(timeout=2)

    @unittest.skipUnless(importlib.util.find_spec("PIL") is not None,
                         "Calc guarded adapter import requires Pillow")
    def test_jsonl_failed_turn_without_usage_stays_unknown_in_prospective_custody(self):
        from datetime import datetime, timedelta, timezone
        from research.live_control.calc_g10_caller_v1 import run_g10_in_durable_allocation
        from research.live_control.integrated_efficiency_protocol_v1 import ARMS, TASKS
        from research.live_control.issue57_v3_prospective_run_v1 import ProspectiveRun

        start = PEER.index('        send({"method": "thread/tokenUsage/updated"')
        end = PEER.index('        send({"method": "turn/completed"', start)
        failed_peer = (PEER[:start] + PEER[end:]).replace(
            '"status": "completed"', '"status": "failed"')
        with tempfile.TemporaryDirectory(prefix="prospective-jsonl-unknown-") as tmp:
            root = Path(tmp)
            workspace = root / "workspace"
            workspace.mkdir()
            image = root / "observation.fixture"
            image.write_bytes(b"synthetic failed-turn observation")
            allocation_path = root / "allocation.json"
            allocation = {
                "allocation_id": "synthetic-prospective-jsonl-unknown-01",
                "host_id": "synthetic-local-host", "owner": "offline-test",
                "exclusive": True,
                "expires_at_utc": (datetime.now(timezone.utc) +
                    timedelta(hours=1)).isoformat(),
                "task_ids": list(TASKS), "arms": list(ARMS),
                "model": "synthetic-model",
                "settings": {"effort": "medium", "provider": "fake"},
                "order_seed": 57,
            }
            allocation_path.write_text(json.dumps(allocation), encoding="utf-8")
            source_root = Path(__file__).resolve().parents[2]
            run = ProspectiveRun(allocation_path, root / "prospective-run",
                source_root=source_root, allocation_verifier=lambda *_args: True)
            ledger = run.create_task_custodian("plain", 0,
                source_sha256=hashlib.sha256(b"synthetic failed-turn source").hexdigest(),
                observation_ids=["observation-jsonl-failed-01"],
                conditions={"fixture": "synthetic-jsonl-failed-turn-no-usage"})
            protocol_path = root / "protocol.jsonl"
            client = CodexAppServerClient(
                [sys.executable, "-B", "-c", failed_peer], cwd=str(workspace),
                journal_path=str(protocol_path))
            model = None
            try:
                client.initialize()
                model = PersistentGroundingModel(
                    root / "session", workspace, node="unused", cli="unused",
                    client=client, path_converter=str,
                    model="synthetic-model", effort="medium")
                provider = V3PersistentGroundingAdapter(model)
                adapters = {
                    "observe_source": lambda _payload: {"sequence": 1},
                    "acquire_anchor": lambda _payload: {"image": str(image)},
                    "anchor_model": lambda _payload: provider(
                        root / "provider-call", "synthetic grounding request", image,
                        "compiled", workspace),
                    "verify_effect": lambda _payload: {"status": "unavailable"},
                }
                spec = {
                    "target": "synthetic Calc save", "route": "cold",
                    "coarse_origin": "caller_provided",
                    "provided_coarse": {"status": "candidate"},
                    "cached_target": None, "local_repair_on": [], "repair_on": [],
                    "session_id": "prospective-jsonl-unknown-01",
                }
                result = run_g10_in_durable_allocation(
                    spec, adapters,
                    lambda _payload: {"interface_id": "synthetic-calc-interface"},
                    object(), {}, ledger,
                    perceive=lambda *_args: {}, verify_effect=lambda *_args: {},
                    proposal_worker=object(), cancelled=lambda: False)
                telemetry = {
                    "local_observations": 1, "durable_calls": 1,
                    "pointer_admissions": 0, "old_target_pointer_admissions": 0,
                    "releases_verified": False, "elapsed_ns": 100,
                    "source_to_completion_ns": None, "input_feedback_ns": [],
                    "repair": {"required": False, "old_reference_status": None,
                        "old_reference_pointer_admissions": 0,
                        "attempted": False, "succeeded": False},
                }
                score = {"submission_count": 0, "exact_submission": False}
                projected = run.record_task("plain", 0, result, score, telemetry,
                    custodian_path=ledger.path)
                lifecycle = [json.loads(line) for line in
                    (root / "prospective-run" / "lifecycle.jsonl").read_text(
                        encoding="utf-8").splitlines()]
                task_event, = [row for row in lifecycle if row["event"] == "task"]
                audit = task_event["payload"]["custody"]["audit"]
                protocol = [json.loads(line) for line in
                    protocol_path.read_text(encoding="utf-8").splitlines()]
                terminal, = [row["message"] for row in protocol
                    if row["direction"] == "received" and
                    row["message"].get("method") == "turn/completed"]
                usage_events = [row for row in protocol
                    if row["direction"] == "received" and
                    row["message"].get("method") == "thread/tokenUsage/updated"]
                self.assertEqual(terminal["params"]["turn"]["status"], "failed")
                self.assertEqual(usage_events, [])
                self.assertEqual(result["outcome"], "CALLER_FAILED")
                self.assertEqual(result["attempt_ledger"][0]["status"], "failed")
                self.assertEqual(result["attempt_ledger"][0]["call_id"], "turn-ledger-1")
                self.assertEqual(result["attempt_ledger"][0]["thread_id"], "thread-ledger-1")
                self.assertIsNone(result["attempt_ledger"][0]["usage"])
                self.assertEqual(result["accounting"]["attempted_calls"], 1)
                self.assertEqual(result["accounting"]["completed_calls"], 0)
                self.assertEqual(result["accounting"]["usage_totals"], {
                    "input_tokens": None, "cached_input_tokens": None,
                    "cache_write_input_tokens": None, "output_tokens": None,
                    "reasoning_output_tokens": None})
                self.assertIsNone(result["task_effect"])
                self.assertFalse(audit["receipt_persisted"])
                self.assertFalse(audit["effect_receipt_persisted"])
                self.assertIsNone(audit["attempt_ledger"][0]["usage"])
                self.assertEqual(audit["status"], "audited")
                self.assertEqual(projected["status"], "HOLD")
                self.assertEqual(projected["reason"],
                                 "failed_attempt_not_representable_in_v1")
                finished = run.finish([])
                self.assertEqual(finished["status"], "HOLD")
                self.assertEqual(len(finished["missing_assignments"]), 17)
                self.assertFalse(json.loads((root / "prospective-run" /
                    "run-manifest.json").read_text(encoding="utf-8"))["dispatch_enabled"])
            finally:
                if model is not None:
                    model.close()
                client.close(timeout=2)

    @unittest.skipUnless(importlib.util.find_spec("PIL") is not None,
                         "Calc guarded adapter import requires Pillow")
    def test_jsonl_success_without_usage_is_held_from_comparison_projection(self):
        from datetime import datetime, timedelta, timezone
        from unittest.mock import patch
        from research.live_control.calc_g10_caller_v1 import run_g10_in_durable_allocation
        from research.live_control.integrated_efficiency_protocol_v1 import ARMS, TASKS
        from research.live_control.issue57_v3_prospective_run_v1 import ProspectiveRun

        start = PEER.index('        send({"method": "thread/tokenUsage/updated"')
        end = PEER.index('        send({"method": "turn/completed"', start)
        success_peer = PEER[:start] + PEER[end:]
        answer = {
            "format": "compiled-form-grounding-v1",
            "field": {"point_space": "source_observation_pixels",
                      "point": {"x": 10, "y": 20},
                      "motion_model": "surface_origin_translation"},
            "submit": {"point_space": "source_observation_pixels",
                       "point": {"x": 30, "y": 40},
                       "motion_model": "surface_origin_translation"},
            "method": {"first_action": "enter_exact_token",
                       "continue_when": "field_pixels_changed_and_submit_revalidated",
                       "second_action": "activate_submit",
                       "complete_when": "submission_pixels_changed_then_independent_score"},
        }
        success_peer = success_peer.replace('"text": "{}"',
                                            '"text": ' + json.dumps(json.dumps(answer)))
        with tempfile.TemporaryDirectory(prefix="prospective-jsonl-success-unknown-") as tmp:
            root = Path(tmp)
            workspace = root / "workspace"
            workspace.mkdir()
            image = root / "observation.fixture"
            image.write_bytes(b"synthetic successful-turn unknown-usage observation")
            allocation_path = root / "allocation.json"
            allocation = {
                "allocation_id": "synthetic-prospective-jsonl-success-unknown-01",
                "host_id": "synthetic-local-host", "owner": "offline-test",
                "exclusive": True,
                "expires_at_utc": (datetime.now(timezone.utc) +
                    timedelta(hours=1)).isoformat(),
                "task_ids": list(TASKS), "arms": list(ARMS),
                "model": "synthetic-model",
                "settings": {"effort": "medium", "provider": "fake"},
                "order_seed": 57,
            }
            allocation_path.write_text(json.dumps(allocation), encoding="utf-8")
            source_root = Path(__file__).resolve().parents[2]
            run = ProspectiveRun(allocation_path, root / "prospective-run",
                source_root=source_root, allocation_verifier=lambda *_args: True)
            ledger = run.create_task_custodian("plain", 0,
                source_sha256=hashlib.sha256(
                    b"synthetic successful-turn unknown-usage source").hexdigest(),
                observation_ids=["observation-success-unknown-01"],
                conditions={"fixture": "synthetic-jsonl-success-no-usage"})
            protocol_path = root / "protocol.jsonl"
            client = CodexAppServerClient(
                [sys.executable, "-B", "-c", success_peer], cwd=str(workspace),
                journal_path=str(protocol_path))
            model = None
            try:
                client.initialize()
                model = PersistentGroundingModel(
                    root / "session", workspace, node="unused", cli="unused",
                    client=client, path_converter=str,
                    model="synthetic-model", effort="medium")
                provider = V3PersistentGroundingAdapter(model)
                adapters = {
                    "observe_source": lambda _payload: {"sequence": 1},
                    "acquire_anchor": lambda _payload: {"image": str(image)},
                    "anchor_model": lambda _payload: provider(
                        root / "provider-call", "synthetic grounding request", image,
                        "compiled", workspace),
                    "final_revalidate": lambda _payload: {"status": "revalidated"},
                    "verify_effect": lambda _payload: {
                        "status": "succeeded", "evidence_ref": "fixture://saved-cell",
                        "evidence_digest": "c" * 64, "effect_scope": "cell-A1 value"},
                }
                spec = {
                    "target": "synthetic Calc save", "route": "cold",
                    "coarse_origin": "caller_provided",
                    "provided_coarse": {"status": "candidate"},
                    "cached_target": None, "local_repair_on": [], "repair_on": [],
                    "session_id": "prospective-jsonl-success-unknown-01",
                }
                execution = {"outcome": "TASK_SUCCEEDED", "completed_transitions": 2,
                             "critical_events": [{"event": "action_terminal",
                                                  "input_dispatched": True}]}
                with patch("research.live_control.calc_g10_caller_v1.run_with_bounded_fresh_proposal",
                           return_value=execution):
                    result = run_g10_in_durable_allocation(
                        spec, adapters,
                        lambda _payload: {"interface_id": "synthetic-calc-interface"},
                        object(), {}, ledger,
                        perceive=lambda *_args: {}, verify_effect=lambda *_args: {},
                        proposal_worker=object(), cancelled=lambda: False)
                telemetry = {
                    "local_observations": 2, "durable_calls": 1,
                    "pointer_admissions": 0, "old_target_pointer_admissions": 0,
                    "releases_verified": True, "elapsed_ns": 100,
                    "source_to_completion_ns": 80, "input_feedback_ns": [],
                    "repair": {"required": False, "old_reference_status": None,
                        "old_reference_pointer_admissions": 0,
                        "attempted": False, "succeeded": False},
                }
                projected = run.record_task("plain", 0, result,
                    {"submission_count": 1, "exact_submission": True}, telemetry,
                    custodian_path=ledger.path)
                lifecycle = [json.loads(line) for line in
                    (root / "prospective-run" / "lifecycle.jsonl").read_text(
                        encoding="utf-8").splitlines()]
                task_event, = [row for row in lifecycle if row["event"] == "task"]
                audit = task_event["payload"]["custody"]["audit"]
                self.assertEqual(result["outcome"], "TASK_SUCCEEDED")
                self.assertEqual(result["task_effect"], "succeeded")
                self.assertEqual(result["attempt_ledger"][0]["status"], "completed")
                self.assertEqual(result["attempt_ledger"][0]["call_id"], "turn-ledger-1")
                self.assertEqual(result["attempt_ledger"][0]["thread_id"], "thread-ledger-1")
                self.assertIsNone(result["attempt_ledger"][0]["usage"])
                self.assertEqual(result["accounting"]["usage_totals"], {
                    "input_tokens": None, "cached_input_tokens": None,
                    "cache_write_input_tokens": None, "output_tokens": None,
                    "reasoning_output_tokens": None})
                self.assertEqual(audit["status"], "audited")
                self.assertTrue(audit["receipt_persisted"])
                self.assertTrue(audit["effect_receipt_persisted"])
                self.assertEqual(audit["attempt_ledger"][0]["usage"], None)
                self.assertEqual(projected["status"], "HOLD")
                self.assertEqual(projected["reason"], "usage_incomplete_or_invalid")
                finished = run.finish([])
                self.assertEqual(finished["status"], "HOLD")
                self.assertEqual(len(finished["missing_assignments"]), 17)
                self.assertFalse(json.loads((root / "prospective-run" /
                    "run-manifest.json").read_text(encoding="utf-8"))["dispatch_enabled"])
                protocol = [json.loads(line) for line in
                    protocol_path.read_text(encoding="utf-8").splitlines()]
                self.assertFalse(any(row["direction"] == "received" and
                    row["message"].get("method") == "thread/tokenUsage/updated"
                    for row in protocol))
            finally:
                if model is not None:
                    model.close()
                client.close(timeout=2)

    @unittest.skipUnless(importlib.util.find_spec("PIL") is not None,
                         "Calc guarded adapter import requires Pillow")
    def test_successful_effect_and_receipts_project_into_prospective_task(self):
        from datetime import datetime, timedelta, timezone
        from unittest.mock import patch
        from research.live_control.calc_g10_caller_v1 import run_g10_in_durable_allocation
        from research.live_control.integrated_efficiency_protocol_v1 import ARMS, TASKS
        from research.live_control.issue57_v3_prospective_run_v1 import ProspectiveRun

        with tempfile.TemporaryDirectory(prefix="prospective-success-effect-") as tmp:
            root = Path(tmp)
            image = root / "observation.fixture"
            image.write_bytes(b"synthetic saved-effect observation")
            allocation_path = root / "allocation.json"
            allocation = {
                "allocation_id": "synthetic-prospective-success-01",
                "host_id": "synthetic-local-host", "owner": "offline-test",
                "exclusive": True,
                "expires_at_utc": (datetime.now(timezone.utc) +
                    timedelta(hours=1)).isoformat(),
                "task_ids": list(TASKS), "arms": list(ARMS),
                "model": "synthetic-model",
                "settings": {"effort": "medium", "provider": "fake"},
                "order_seed": 57,
            }
            allocation_path.write_text(json.dumps(allocation), encoding="utf-8")
            source_root = Path(__file__).resolve().parents[2]
            run = ProspectiveRun(allocation_path, root / "prospective-run",
                source_root=source_root, allocation_verifier=lambda *_args: True)
            ledger = run.create_task_custodian("plain", 0,
                source_sha256=hashlib.sha256(b"synthetic success task source").hexdigest(),
                observation_ids=["observation-success-01"],
                conditions={"fixture": "synthetic-success-effect"})
            usage = {"input_tokens": 120, "cached_input_tokens": 20,
                     "cache_write_input_tokens": 0, "output_tokens": 12,
                     "reasoning_output_tokens": 4}
            adapters = {
                "observe_source": lambda _payload: {"sequence": 1},
                "acquire_anchor": lambda _payload: {"image": str(image)},
                "anchor_model": lambda _payload: {
                    "call_id": "turn-success-01", "thread_id": "thread-success-01",
                    "output": {"status": "target_reference", "target": "cell-A1"},
                    "usage": usage, "requested_model": "synthetic-model",
                    "requested_effort": "medium", "cost": 0.01,
                    "visible_images_submitted": 1, "wait_ns": 50},
                "final_revalidate": lambda _payload: {"status": "revalidated"},
                "verify_effect": lambda _payload: {
                    "status": "succeeded", "evidence_ref": "fixture://saved-cell",
                    "evidence_digest": "a" * 64, "effect_scope": "cell-A1 value"},
            }
            spec = {
                "target": "synthetic Calc save", "route": "cold",
                "coarse_origin": "caller_provided",
                "provided_coarse": {"status": "candidate"},
                "cached_target": None, "local_repair_on": [], "repair_on": [],
                "session_id": "prospective-success-effect-01",
            }
            execution = {"outcome": "TASK_SUCCEEDED", "completed_transitions": 2,
                         "critical_events": [{"event": "action_terminal",
                                              "input_dispatched": True}]}
            with patch("research.live_control.calc_g10_caller_v1.run_with_bounded_fresh_proposal",
                       return_value=execution):
                result = run_g10_in_durable_allocation(
                    spec, adapters,
                    lambda _payload: {"interface_id": "synthetic-calc-interface"},
                    object(), {}, ledger,
                    perceive=lambda *_args: {}, verify_effect=lambda *_args: {},
                    proposal_worker=object(), cancelled=lambda: False)
            projected = run.record_task("plain", 0, result,
                {"submission_count": 1, "exact_submission": True}, {
                    "local_observations": 2, "durable_calls": 1,
                    "pointer_admissions": 0, "old_target_pointer_admissions": 0,
                    "releases_verified": True, "elapsed_ns": 100,
                    "source_to_completion_ns": 80, "input_feedback_ns": [],
                    "repair": {"required": False, "old_reference_status": None,
                        "old_reference_pointer_admissions": 0,
                        "attempted": False, "succeeded": False},
                }, custodian_path=ledger.path)
            task_event, = [json.loads(line) for line in
                (root / "prospective-run" / "lifecycle.jsonl").read_text(
                    encoding="utf-8").splitlines()
                if json.loads(line)["event"] == "task"]
            audit = task_event["payload"]["custody"]["audit"]
            self.assertEqual(result["outcome"], "TASK_SUCCEEDED")
            self.assertEqual(result["task_effect"], "succeeded")
            self.assertEqual(projected["status"], "projected")
            self.assertTrue(audit["receipt_persisted"])
            self.assertTrue(audit["effect_receipt_persisted"])
            self.assertEqual(audit["attempt_ledger"][0]["usage"], usage)
            finished = run.finish([])
            self.assertEqual(finished["status"], "HOLD")
            self.assertEqual(len(finished["missing_assignments"]), 17)

    @unittest.skipUnless(importlib.util.find_spec("PIL") is not None,
                         "Calc guarded adapter import requires Pillow")
    def test_complete_synthetic_three_arm_run_audits_all_18_custodians(self):
        from datetime import datetime, timedelta, timezone
        from research.live_control.integrated_efficiency_protocol_v1 import (
            ARMS, EXPECTED_MODEL_CALLS, TASKS,
        )
        from research.live_control.issue57_v3_prospective_run_v1 import ProspectiveRun

        with tempfile.TemporaryDirectory(prefix="prospective-three-arm-complete-") as tmp:
            root = Path(tmp)
            allocation_path = root / "allocation.json"
            allocation = {
                "allocation_id": "synthetic-prospective-three-arm-01",
                "host_id": "synthetic-local-host", "owner": "offline-test",
                "exclusive": True,
                "expires_at_utc": (datetime.now(timezone.utc) +
                    timedelta(hours=1)).isoformat(),
                "task_ids": list(TASKS), "arms": list(ARMS),
                "model": "synthetic-model",
                "settings": {"effort": "medium", "provider": "fake"},
                "order_seed": 57,
            }
            allocation_path.write_text(json.dumps(allocation), encoding="utf-8")
            source_root = Path(__file__).resolve().parents[2]
            run = ProspectiveRun(allocation_path, root / "prospective-run",
                source_root=source_root, allocation_verifier=lambda *_args: True)
            usage_by_arm = {
                "plain": 1000, "ephemeral": 1200, "persistent": 10,
            }
            for arm in ARMS:
                run.record_preflight(arm, {
                    "call_id": "preflight-" + arm,
                    "stage": "schema_preflight", "requested_model": "synthetic-model",
                    "requested_effort": "medium",
                    "usage": {"input_tokens": 10, "cached_input_tokens": 0,
                        "cache_write_input_tokens": 0, "output_tokens": 1,
                        "reasoning_output_tokens": 0},
                    "model_visible_images": 0,
                })

            for arm in ARMS:
                for index, task_id in enumerate(TASKS):
                    calls = []
                    for call_index in range(EXPECTED_MODEL_CALLS[arm][index]):
                        call_id = f"{arm}-{task_id}-{call_index}"
                        call_usage = {"input_tokens": usage_by_arm[arm],
                            "cached_input_tokens": 0, "cache_write_input_tokens": 0,
                            "output_tokens": 10, "reasoning_output_tokens": 1}
                        calls.append({
                            "attempt_id": "attempt-" + call_id,
                            "stage": "anchor_model", "status": "completed",
                            "call_id": call_id, "thread_id": "thread-" + call_id,
                            "requested_model": "synthetic-model",
                            "requested_effort": "medium", "usage": call_usage,
                            "cost": None, "visible_images_submitted": 1,
                            "wait_ns": 100,
                        })
                    coverage = {field: len(calls) for field in (
                        "input_tokens", "cached_input_tokens",
                        "cache_write_input_tokens", "output_tokens",
                        "reasoning_output_tokens")}
                    totals = {field: sum(row["usage"][field] for row in calls)
                              for field in coverage}
                    model_calls = [{key: row[key] for key in (
                        "attempt_id", "call_id", "stage", "requested_model",
                        "requested_effort", "usage", "cost",
                        "visible_images_submitted", "wait_ns")}
                        for row in calls]
                    accounting = {
                        "attempted_calls": len(calls),
                        "completed_calls": len(calls),
                        "duplicate_call_ids": [], "usage_totals": totals,
                        "usage_coverage": coverage,
                        "visible_images_submitted": len(calls),
                        "visible_image_coverage": len(calls),
                        "model_wait_ns": 100 * len(calls),
                        "model_wait_coverage": len(calls),
                        "cost_coverage": 0,
                        "cost": 0 if not calls else None,
                        "cached_input_semantics":
                            "subset of input_tokens; never added to input total",
                    }
                    result = {
                        "outcome": "TASK_SUCCEEDED", "task_effect": "succeeded",
                        "attempt_ledger": calls, "model_call_ledger": model_calls,
                        "accounting": accounting,
                        "effect_receipt": {"status": "succeeded"},
                    }
                    source_sha = hashlib.sha256(
                        f"synthetic-task-source-{arm}-{task_id}".encode()).hexdigest()
                    ledger = run.create_task_custodian(arm, index,
                        source_sha256=source_sha,
                        observation_ids=[f"obs-{arm}-{task_id}"],
                        conditions={"fixture": "synthetic-complete-trace"})
                    ledger.bind_interface({"interface_id": f"if-{arm}-{task_id}"})
                    ledger.persist_execution_receipt({
                        "status": "completed", "synthetic": True})
                    ledger.persist_effect_receipt({
                        "status": "succeeded", "evidence_ref": f"fixture://{task_id}"})
                    ledger.finalize(result)
                    repair_required = arm == "persistent" and index == 3
                    projected = run.record_task(arm, index, result,
                        {"submission_count": 1, "exact_submission": True}, {
                            "local_observations": 2, "durable_calls": 1,
                            "pointer_admissions": 2,
                            "old_target_pointer_admissions": 0,
                            "releases_verified": True,
                            "elapsed_ns": 300 if arm == "persistent" else 1000,
                            "source_to_completion_ns": 250,
                            "input_feedback_ns": [100, 120],
                            "repair": ({"required": True,
                                "old_reference_status": "missing",
                                "old_reference_pointer_admissions": 0,
                                "attempted": True, "succeeded": True}
                                if repair_required else {
                                    "required": False,
                                    "old_reference_status": None,
                                    "old_reference_pointer_admissions": 0,
                                    "attempted": False, "succeeded": False}),
                        }, custodian_path=ledger.path)
                    self.assertEqual(projected["status"], "projected",
                                     (arm, index, projected))

            discoveries = json.loads((source_root / "research/live_control" /
                "integrated_efficiency_discoveries_v1.json").read_text(
                    encoding="utf-8"))
            lifecycle = [json.loads(line) for line in
                (root / "prospective-run" / "lifecycle.jsonl").read_text(
                    encoding="utf-8").splitlines()]
            task_events = [row for row in lifecycle if row["event"] == "task"]
            self.assertEqual(len(task_events), 18)
            self.assertTrue(all(row["payload"]["custody"]["status"] == "audited"
                                for row in task_events))
            result = run.finish(discoveries)
            self.assertEqual(result["status"], "ready_for_frozen_evaluator", result)
            self.assertEqual(result["adjudication"]["evaluation"]["disposition"],
                             "RETAIN")
            self.assertEqual(result["missing_assignments"], [])
            self.assertEqual(len(result["adjudication"]["trace"]["arms"]["plain"]), 6)
            manifest = json.loads((root / "prospective-run" /
                "run-manifest.json").read_text(encoding="utf-8"))
            self.assertFalse(manifest["dispatch_enabled"])
            evaluation = result["adjudication"]["evaluation"]
            print("SYNTHETIC_R06 " + json.dumps({
                "status": result["status"],
                "disposition": evaluation["disposition"],
                "missing_assignments": len(result["missing_assignments"]),
                "custody_audited": len(task_events),
                "arms": {arm: {
                    "correct": evaluation["arms"][arm]["correct"],
                    "input_tokens_final": evaluation["arms"][arm][
                        "cumulative_input_tokens"][-1],
                    "planner_generations_final": evaluation["arms"][arm][
                        "cumulative_planner_generations"][-1],
                    "elapsed_ns": evaluation["arms"][arm]["elapsed_ns"],
                } for arm in ARMS},
                "dispatch_enabled": manifest["dispatch_enabled"],
            }, sort_keys=True))


if __name__ == "__main__":
    unittest.main()
