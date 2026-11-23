"""Join synthetic JSONL provider accounting to compiled GUI and durable custody."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import sys
import time
import unittest

from research.live_control.adaptive_acquisition_caller_v3 import _effect_receipt
from research.live_control.calc_durable_allocation_v1 import (
    DurableCalcAllocation,
    audit_allocation,
)
from research.live_control.codex_app_server_client_v2 import CodexAppServerClient
from research.live_control.integrated_efficiency_app_server_model_v1 import (
    PersistentGroundingModel,
)
from research.live_control.integrated_efficiency_compiled_execution_v2 import (
    run_compiled_interface_in_caller,
)
from research.live_control.test_adaptive_acquisition_compiled_gui_v1 import (
    compiled_interface,
)
from research.live_control.test_grounding_appserver_usage_transport import PEER
from research.live_control.v3_persistent_grounding_adapter_v1 import (
    V3PersistentGroundingAdapter,
)


ANSWER = {
    "format": "compiled-form-grounding-v1",
    "field": {
        "point_space": "source_observation_pixels",
        "point": {"x": 10, "y": 20},
        "motion_model": "surface_origin_translation",
    },
    "submit": {
        "point_space": "source_observation_pixels",
        "point": {"x": 30, "y": 40},
        "motion_model": "surface_origin_translation",
    },
    "method": {
        "first_action": "enter_exact_token",
        "continue_when": "field_pixels_changed_and_submit_revalidated",
        "second_action": "activate_submit",
        "complete_when": "submission_pixels_changed_then_independent_score",
    },
}
USAGE = {
    "input_tokens": 1234,
    "cached_input_tokens": 234,
    "cache_write_input_tokens": 0,
    "output_tokens": 56,
    "reasoning_output_tokens": 12,
}
MODE = os.environ.get("ISSUE57_COMPOSITION_MODE")
EVIDENCE_ROOT = Path(os.environ.get("ISSUE57_COMPOSITION_EVIDENCE", ""))
if MODE not in {"normal", "optimized"} or not EVIDENCE_ROOT.is_absolute():
    raise RuntimeError("frozen mode and absolute evidence root are required")


def _success_peer():
    answer_text = json.dumps(json.dumps(ANSWER, separators=(",", ":")))
    peer = PEER.replace('"text": "{}"', '"text": ' + answer_text)
    if peer == PEER:
        raise RuntimeError("synthetic App Server answer template was not replaced")
    return peer


class StatefulForm:
    def __init__(self, changed_intermediate):
        self.changed_intermediate = changed_intermediate
        self.phase = 0
        self.sequence = 0
        self.actions = []
        self.admissions = []
        self.release_receipts = []
        self.local_effect_checks = []
        self.outer_scores = []

    def observe(self, _request):
        self.sequence += 1
        return {
            "sequence": self.sequence,
            "captured_ns": time.perf_counter_ns(),
            "surface": "form",
            "predicates": {
                "phase": self.phase,
                "submit_present": not (
                    self.changed_intermediate and self.phase == 1
                ),
            },
            "evidence_ref": f"fixture://{MODE}/frame-{self.sequence}",
            "evidence_digest": hashlib.sha256(
                f"{MODE}:{self.phase}:{self.sequence}".encode()
            ).hexdigest(),
        }

    def admit(self, request):
        self.admissions.append(request["action"])
        return {
            "eligible": True,
            "status": "revalidated",
            "authorization": f"one-use-{len(self.admissions)}",
            "expected_sequence": request["observation"]["sequence"],
            "valid_until_ns": time.perf_counter_ns() + 30_000_000_000,
        }

    def execute(self, request):
        operation = request["operation"]
        self.actions.append(operation)
        if operation == "enter_value":
            self.phase = 1
        elif operation == "submit":
            self.phase = 2
        else:
            raise AssertionError(f"unexpected operation: {operation}")
        release = {
            "verified": True,
            "keys_down": [],
            "buttons_down": [],
        }
        self.release_receipts.append(release)
        return {
            "status": "completed",
            "action_id": f"action-{len(self.actions)}",
            "effect_ref": f"fixture://{MODE}/effect-{len(self.actions)}",
            "release": release,
        }

    def verify_local_effect(self, request):
        self.local_effect_checks.append(request["action"])
        return {
            "status": "succeeded",
            "evidence_ref": request["observation"]["evidence_ref"],
        }

    def score_task_independently(self, _request):
        self.outer_scores.append({"phase": self.phase, "actions": list(self.actions)})
        success = self.phase == 2 and self.actions == ["enter_value", "submit"]
        return {
            "status": "succeeded" if success else "failed",
            "evidence_ref": f"fixture://{MODE}/independent-task-score",
            "evidence_digest": hashlib.sha256(
                f"independent:{MODE}:{self.phase}:{self.actions}".encode()
            ).hexdigest(),
            "effect_scope": "whole-form-submission",
        }


def _run_case(case_name, *, changed_intermediate):
    case_root = EVIDENCE_ROOT / MODE / case_name
    case_root.mkdir(parents=True, exist_ok=False)
    workspace = case_root / "workspace"
    workspace.mkdir()
    image = case_root / "source-observation.fixture"
    image.write_bytes(f"synthetic form observation {MODE} {case_name}".encode())
    allocation_root = case_root / "allocation"
    allocation_root.mkdir()
    frozen_task_source = hashlib.sha256(
        b"issue57-currentmain-provider-compiled-composition-r01/form-submit-v1"
    ).hexdigest()
    source_files = (
        "research/live_control/adaptive_acquisition_caller_v3.py",
        "research/live_control/v3_persistent_grounding_adapter_v1.py",
        "research/live_control/integrated_efficiency_app_server_model_v1.py",
        "research/live_control/integrated_efficiency_compiled_execution_v2.py",
        "research/live_control/calc_durable_allocation_v1.py",
        "runtime/core_v1/compiled_gui.py",
    )
    source_hashes = {
        name: hashlib.sha256((Path.cwd() / name).read_bytes()).hexdigest()
        for name in source_files
    }
    durable = DurableCalcAllocation(
        allocation_root,
        f"synthetic-{MODE}-{case_name}",
        source_sha256=frozen_task_source,
        observation_ids=[f"source-observation-{MODE}-{case_name}"],
        source_hashes=source_hashes,
        conditions={
            "experiment": "issue57-provider-compiled-currentmain-r01",
            "mode": MODE,
            "case": case_name,
            "provider": "in-process synthetic JSONL peer",
            "ui": "stateful deterministic callback fixture",
            "dispatch_enabled": False,
        },
    )

    protocol_path = case_root / "protocol.jsonl"
    client = CodexAppServerClient(
        [sys.executable, "-B", "-c", _success_peer()],
        cwd=str(workspace),
        journal_path=str(protocol_path),
    )
    model = None
    form = StatefulForm(changed_intermediate)
    caller_events = []
    runtime_events = []
    try:
        client.initialize()
        model = PersistentGroundingModel(
            case_root / "session",
            workspace,
            node="unused",
            cli="unused",
            model="synthetic-model",
            effort="medium",
            client=client,
            path_converter=str,
        )
        provider = V3PersistentGroundingAdapter(
            model,
            output_projector=lambda grounding: {
                "status": "target_reference",
                "target": grounding,
            },
        )

        def anchor_model(_payload):
            return provider(
                case_root / "provider-call",
                "Ground the synthetic form target for this frozen task.",
                image,
                "compiled",
                workspace,
            )

        def interface_for_target(payload):
            target = payload["target"]
            target_digest = hashlib.sha256(json.dumps(
                target, sort_keys=True, separators=(",", ":")
            ).encode()).hexdigest()
            interface = compiled_interface()
            interface["interface_id"] = "provider-grounded-" + target_digest[:16]
            interface["symbols"]["form"]["target_reference"] = target_digest
            interface["symbols"]["form"]["identity_predicate"] = "phase"
            durable.bind_interface(interface)
            return interface

        def caller_journal(event):
            durable.append_event("caller_event", event)
            caller_events.append(event)

        def durable_task_score(request):
            effect = form.score_task_independently(request)
            durable.persist_effect_receipt(_effect_receipt(effect))
            return effect

        caller_adapters = {
            "observe_source": lambda _payload: {
                "evidence_ref": f"fixture://{MODE}/{case_name}/source",
                "evidence_digest": frozen_task_source,
            },
            "acquire_anchor": lambda _payload: {"image": str(image)},
            "anchor_model": anchor_model,
            "final_revalidate": lambda _payload: {"status": "revalidated"},
            "verify_effect": durable_task_score,
            "journal": caller_journal,
        }
        spec = {
            "target": "submit the synthetic form exactly once",
            "route": "cold",
            "coarse_origin": "caller_provided",
            "provided_coarse": {"status": "candidate", "candidate": "form"},
            "cached_target": None,
            "local_repair_on": [],
            "repair_on": [],
            "session_id": f"synthetic-{MODE}-{case_name}",
        }
        execution_adapters = {
            "observe": form.observe,
            "admit": form.admit,
            "execute": form.execute,
            "verify_effect": form.verify_local_effect,
            "cancelled": lambda: False,
            "journal": lambda event: (
                durable.append_event("compiled_event", event),
                runtime_events.append(event),
            ),
        }
        result = run_compiled_interface_in_caller(
            spec,
            caller_adapters,
            interface_for_target,
            execution_adapters,
            on_receipt=durable.persist_execution_receipt,
        )
        durable.finalize(result)
        audit = audit_allocation(durable.path)
        protocol = [json.loads(line) for line in protocol_path.read_text(
            encoding="utf-8").splitlines()]
        usage_events = [row["message"] for row in protocol
            if row["direction"] == "received" and
            row["message"].get("method") == "thread/tokenUsage/updated"]
        provider_attempts = [row for row in result["attempt_ledger"]
                             if row["stage"] == "anchor_model"]
        summary = {
            "mode": MODE,
            "case": case_name,
            "outcome": result["outcome"],
            "reason": result["reason"],
            "task_effect": result["task_effect"],
            "delivery": result["delivery"],
            "comparison_class": result["comparison"]["class"],
            "accounting": result["accounting"],
            "attempt_ledger": result["attempt_ledger"],
            "model_call_ledger": result["model_call_ledger"],
            "compiled_receipt": result["compiled_execution_receipt"],
            "independent_score_calls": form.outer_scores,
            "actions": form.actions,
            "admissions": form.admissions,
            "release_receipts": form.release_receipts,
            "local_effect_checks": form.local_effect_checks,
            "protocol_usage_events": usage_events,
            "durable_audit": audit,
            "durable_allocation": str(durable.path.relative_to(EVIDENCE_ROOT)),
            "caller_journal_event_count": len(caller_events),
            "compiled_journal_event_count": len(runtime_events),
        }
        summary_path = case_root / "scenario-summary.json"
        summary_path.write_bytes((json.dumps(summary, indent=2) + "\n").encode())
        return summary
    finally:
        if model is not None:
            model.close()
        client.close(timeout=2)


class ProviderCompiledCompositionTest(unittest.TestCase):
    def test_success_and_changed_intermediate_are_joined_to_provider_usage_and_custody(self):
        positive = _run_case("positive", changed_intermediate=False)
        self.assertEqual(positive["outcome"], "TASK_SUCCEEDED", positive)
        self.assertEqual(positive["task_effect"], "succeeded")
        self.assertEqual(positive["accounting"]["attempted_calls"], 1)
        self.assertEqual(positive["accounting"]["completed_calls"], 1)
        self.assertEqual(positive["accounting"]["usage_totals"], USAGE)
        self.assertEqual(positive["accounting"]["cost"], None)
        self.assertEqual(len(positive["attempt_ledger"]), 1)
        attempt = positive["attempt_ledger"][0]
        self.assertEqual(attempt["call_id"], "turn-ledger-1")
        self.assertEqual(attempt["thread_id"], "thread-ledger-1")
        self.assertEqual(attempt["usage"], USAGE)
        self.assertEqual(positive["compiled_receipt"]["outcome"], "TASK_SUCCEEDED")
        self.assertEqual(positive["compiled_receipt"]["completed_transitions"], 2)
        self.assertEqual(positive["actions"], ["enter_value", "submit"])
        self.assertEqual(positive["admissions"], ["enter", "submit"])
        self.assertEqual(len(positive["release_receipts"]), 2)
        self.assertTrue(all(row["verified"] and not row["keys_down"] and
                            not row["buttons_down"]
                            for row in positive["release_receipts"]))
        self.assertEqual(len(positive["independent_score_calls"]), 1)
        self.assertEqual(positive["durable_audit"]["status"], "audited")
        self.assertEqual(positive["durable_audit"]["outcome"], "TASK_SUCCEEDED")
        self.assertTrue(positive["durable_audit"]["receipt_persisted"])
        self.assertTrue(positive["durable_audit"]["effect_receipt_persisted"])
        self.assertEqual(len(positive["protocol_usage_events"]), 1)

        changed = _run_case("changed-intermediate", changed_intermediate=True)
        self.assertEqual(changed["outcome"], "EXECUTION_INCOMPLETE", changed)
        self.assertEqual(changed["reason"], "unknown_state")
        self.assertEqual(changed["delivery"], "confirmed_partial")
        self.assertIsNone(changed["task_effect"])
        self.assertEqual(changed["compiled_receipt"]["outcome"], "SAFE_YIELD")
        self.assertEqual(changed["compiled_receipt"]["completed_transitions"], 1)
        self.assertEqual(changed["actions"], ["enter_value"])
        self.assertEqual(changed["admissions"], ["enter"])
        self.assertEqual(len(changed["release_receipts"]), 1)
        self.assertTrue(changed["release_receipts"][0]["verified"])
        self.assertEqual(changed["independent_score_calls"], [])
        self.assertEqual(changed["accounting"]["usage_totals"], USAGE)
        self.assertEqual(changed["durable_audit"]["status"], "audited")
        self.assertEqual(changed["durable_audit"]["outcome"], "EXECUTION_INCOMPLETE")
        self.assertTrue(changed["durable_audit"]["receipt_persisted"])
        self.assertFalse(changed["durable_audit"]["effect_receipt_persisted"])
        self.assertEqual(len(changed["protocol_usage_events"]), 1)
        print("COMPOSITION_SCENARIOS " + json.dumps({
            "positive": {
                "outcome": positive["outcome"],
                "actions": positive["actions"],
                "usage": positive["accounting"]["usage_totals"],
                "custody": positive["durable_audit"]["status"],
            },
            "changed_intermediate": {
                "outcome": changed["outcome"],
                "reason": changed["reason"],
                "actions": changed["actions"],
                "usage": changed["accounting"]["usage_totals"],
                "custody": changed["durable_audit"]["status"],
            },
        }, sort_keys=True))


if __name__ == "__main__":
    unittest.main()
