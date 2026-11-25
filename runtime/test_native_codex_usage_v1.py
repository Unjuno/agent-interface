"""Offline checking of cache-write omissions at the native preview boundary."""
import hashlib
import json
from contextlib import nullcontext
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from runtime import golden_desktop_demo_v2 as demo
from integrated_efficiency_app_server_model_v1 import (
    GroundingCallError, PersistentGroundingModel, USAGE_MAP, per_turn_usage,
)
from native_codex_usage_v1 import CACHE_WRITE, POLICY, accounting


USAGE = {"input_tokens": 8, "cached_input_tokens": 2, CACHE_WRITE: 0,
         "output_tokens": 3, "reasoning_output_tokens": 1}
PARTIAL = {key: count for key, count in USAGE.items() if key != CACHE_WRITE}
ANSWER = {
    "format": "compiled-form-grounding-v1",
    "field": {"point_space": "source_observation_pixels",
              "point": {"x": 10, "y": 20}, "motion_model": "surface_origin_translation"},
    "submit": {"point_space": "source_observation_pixels",
               "point": {"x": 30, "y": 40}, "motion_model": "surface_origin_translation"},
    "method": {"first_action": "enter_exact_token",
               "continue_when": "field_pixels_changed_and_submit_revalidated",
               "second_action": "activate_submit",
               "complete_when": "submission_pixels_changed_then_independent_score"},
}


def provider_usage(usage):
    return {"last": {source: usage[target] for source, target in USAGE_MAP.items() if target in usage}}


def put(root, name, value):
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = value if type(value) is list else [value]
    path.write_text("".join(json.dumps(line) + "\n" for line in lines), encoding="utf-8")


def tasks_for(call_usages):
    repair = {"required": True, "old_reference_status": "missing",
              "old_reference_pointer_admissions": 0, "attempted": True, "succeeded": True}
    calls = [{"call_id": "turn-" + str(index + 1), "usage": usage,
              "requested_model": "gpt-5.6-luna", "requested_effort": "low"}
             for index, usage in enumerate(call_usages)]
    return [{"task_id": f"task-{index + 1}", "exact_submission": True, "releases_verified": True,
             "repair": repair if index == 3 else {"required": False},
             "route": "repair" if index == 3 else "cold" if index == 0 else "reuse",
             "model_calls": [calls[0]] if index == 0 else [calls[1]] if index == 3 else [],
             "model_visible_images": int(index in (0, 3)),
             "old_target_pointer_admissions": 0,
             "input_feedback_ns": [100_000_000], "elapsed_ns": 1_000_000_000}
            for index in range(6)]


class NativeCodexUsageTests(unittest.TestCase):
    def test_app_server_omission_does_not_equal_zero_and_null_is_malformed(self):
        self.assertEqual(per_turn_usage(provider_usage(PARTIAL), allow_missing_cache_write=True),
                         PARTIAL)
        self.assertEqual(per_turn_usage(provider_usage(USAGE), allow_missing_cache_write=True), USAGE)
        with self.assertRaisesRegex(ValueError, "missing app-server usage"):
            per_turn_usage(provider_usage(PARTIAL))
        for invalid in ({**USAGE, CACHE_WRITE: None}, {**USAGE, CACHE_WRITE: True},
                        {**PARTIAL, "cached_input_tokens": 9},
                        {**PARTIAL, "reasoning_output_tokens": 4},
                        {key: count for key, count in PARTIAL.items() if key != "output_tokens"}):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                per_turn_usage(provider_usage(invalid), allow_missing_cache_write=True)

    def test_native_grounding_with_required_counts_preserves_optional_omission(self):
        with TemporaryDirectory() as td:
            root = Path(td)
            client = Mock()
            client.start_thread.return_value = {"thread": {"id": "thread"}}
            client.start_turn.return_value = {"turn": {"id": "turn"}}
            model = PersistentGroundingModel(root / "session", root, client=client,
                                             path_converter=str, allow_missing_cache_write=True)
            completed = SimpleNamespace(answer_eligible=True, usage=provider_usage(PARTIAL),
                                        answer=ANSWER, status="completed")
            image = root / "image"
            image.write_bytes(b"fixture-image")
            with patch.object(model.planner, "await_turn", return_value=completed):
                result = model.call(root / "call", "fixture", image, "compiled", root)
            request = json.loads((root / "call" / "request.json").read_bytes())
            self.assertEqual(request["image_sha256"], hashlib.sha256(b"fixture-image").hexdigest())
            self.assertEqual(result["usage"], PARTIAL)
            evidence = json.loads((root / "call" / "result.json").read_bytes())
            self.assertNotIn(CACHE_WRITE, evidence["usage"])
            self.assertEqual(evidence["provider_usage"], provider_usage(PARTIAL))
            self.assertEqual(client.start_thread.call_args.kwargs["config"],
                             {"project_doc_max_bytes": 0, "model_reasoning_effort": "low"})
            self.assertEqual(client.start_turn.call_count, 1)

    def test_missing_required_usage_keeps_native_grounding_held(self):
        with TemporaryDirectory() as td:
            root = Path(td)
            client = Mock()
            client.start_thread.return_value = {"thread": {"id": "thread"}}
            client.start_turn.return_value = {"turn": {"id": "turn"}}
            model = PersistentGroundingModel(root / "session", root, client=client,
                                             path_converter=str, allow_missing_cache_write=True)
            completed = SimpleNamespace(answer_eligible=True, usage=None)
            image = root / "image"
            image.write_bytes(b"fixture-image")
            with patch.object(model.planner, "await_turn", return_value=completed):
                with self.assertRaises(GroundingCallError):
                    model.call(root / "call", "fixture", image, "compiled", root)
            self.assertEqual(client.start_turn.call_count, 1)

    def test_golden_run_retains_partial_usage_without_claiming_pass(self):
        with TemporaryDirectory() as td:
            root = Path(td)
            implementation = SimpleNamespace()
            implementation.preflight_call = lambda *_: {"call_id": "preflight", "usage": USAGE}
            implementation.run_arm = Mock(return_value=(tasks_for([PARTIAL, USAGE]), {"success": True}))
            model = nullcontext(SimpleNamespace(thread_id="thread", calls=2, call=Mock()))
            config = {"chromium": root / "browser", "windows_codex_exe": root / "codex.exe"}
            with patch.object(demo.base, "doctor", return_value={"passed": True}), \
                 patch.object(demo.base, "configuration", return_value=config), \
                 patch.object(demo.base, "configure_research_modules",
                              return_value=(implementation, object)), \
                 patch.object(demo.base, "windows_arg", return_value=r"C:\allocation"):
                report = demo.run_live(root / "out", 1, grounding_model_type=Mock(return_value=model))
            recorded = json.loads((root / "out" / "doctor.json").read_bytes())
            self.assertEqual(recorded["native_run_root"], report["environment"]["native_run_root"])
            self.assertTrue(report["functional_passed"])
            self.assertFalse(report["passed"])
            self.assertIsNone(report["usage"][CACHE_WRITE])
            self.assertEqual(report["usage_coverage"][CACHE_WRITE], 2)
            self.assertEqual(report["usage"]["input_tokens"], 24)
            self.assertEqual(report["usage_status"], "partial")

    def test_audit_recomputes_native_usage_and_rejects_zero_fabrication(self):
        cases = ("complete", "partial", "late_usage", "grounding_zero", "preflight_zero",
                 "missing_protocol", "erased_labels", "failed_preflight", "extra_prepared",
                 "ack_before_sent", "usage_before_sent", "completion_before_sent", "boolean_zero",
                 "argv_mismatch", "cache_mismatch", "exec_wrong_model", "exec_wrong_effort",
                 "exec_image", "thread_wrong_model", "thread_wrong_effort",
                 "turn_wrong_model", "turn_wrong_effort", "turn_missing_image",
                 "same_unrelated_images", "changed_image_bytes", "second_completed_first",
                 "double_preflight_start", "completion_error", "completion_empty_items",
                 "zero_edited_journal_and_ledger", "result_usage_zero_only",
                 "relocated_provider_root", "mismatched_preflight_root", "unc_root",
                 "unc_case_substitution")
        for mode in cases:
            with self.subTest(mode=mode), TemporaryDirectory() as td:
                out = Path(td)
                self.make_audit_packet(out, mode)
                audit = demo.base.audit_live(out)
                if mode in ("complete", "partial", "late_usage", "unc_root"):
                    self.assertTrue(audit["functional_passed"])
                    complete = mode != "partial"
                    self.assertEqual(audit["passed"], complete)
                    self.assertEqual(audit["usage_status"], "complete" if complete else "partial")
                    self.assertEqual(audit["usage"]["output_tokens"], 9)
                    self.assertEqual(audit["usage_coverage"][CACHE_WRITE], 3 if complete else 2)
                    self.assertEqual(audit["usage"][CACHE_WRITE], 4 if complete else None)
                else:
                    self.assertFalse(audit["passed"])
                    self.assertFalse(audit["functional_passed"])
                    self.assertEqual(audit["usage_status"], "unverified")

    def make_audit_packet(self, out, mode):
        raw_preflight = PARTIAL if mode == "preflight_zero" else {**USAGE, CACHE_WRITE: 4}
        raw_grounding = [PARTIAL, USAGE] if mode in ("partial", "grounding_zero", "erased_labels") else [USAGE, USAGE]
        preflight_report = USAGE if mode == "preflight_zero" else raw_preflight
        task_report = [USAGE, USAGE] if mode in ("grounding_zero", "erased_labels") else raw_grounding
        summary = accounting([{"usage": usage} for usage in [preflight_report, *task_report]])
        report = {"passed": summary["usage_status"] == "complete", "functional_passed": True,
                  "accounting_policy": POLICY, **summary, "tasks": tasks_for(task_report),
                  "grounding_thread_id": "thread", "grounding_call_ids": ["turn-1", "turn-2"],
                  "planner_generations_including_preflight": 3, "model_visible_images": 2,
                  "old_target_pointer_admissions": 0, "scope": "synthetic"}
        if mode == "erased_labels":
            report.pop("accounting_policy")
        if mode == "boolean_zero":
            report["tasks"][0]["model_calls"][0]["usage"] = {**task_report[0], CACHE_WRITE: False}
        exe = r"C:\Program Files\Codex\codex.exe"
        unc = mode in ("unc_root", "unc_case_substitution")
        windows_root = r"\\wsl.localhost\Ubuntu\home\owner\allocation" if unc else r"C:\allocation"
        wsl_root = "/home/owner/allocation" if unc else "/mnt/c/allocation"
        launch_root = r"C:\different" if mode == "mismatched_preflight_root" else windows_root
        native = {"windows_path": exe, "version": "codex-cli fixture", "executable_sha256": "a" * 64}
        root_receipt = {"wsl_path": wsl_root, "windows_path": launch_root}
        doctor = {"passed": True, "configuration": {
            "windows_codex_exe": "/mnt/c/Program Files/Codex/codex.exe"}, "native_codex": native,
            "native_run_root": root_receipt}
        put(out, "doctor.json", doctor)
        report["environment"] = doctor
        if mode == "erased_labels":
            report.pop("environment")
        put(out, "golden-report.json", report)
        identity = {"cli_transport": "windows-native-codex-exe", "usage_policy": POLICY,
                    "cli_windows_path": exe, "cli_version": native["version"],
                    "cli_executable_sha256": native["executable_sha256"], "requested_model": "gpt-5.6-luna",
                    "requested_effort": "low", "runner_sha256": "b" * 64, "schema_sha256": "c" * 64,
                    "instructions_sha256": "d" * 64}
        key = hashlib.sha256(json.dumps(identity, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        result = {"identity": identity, "compatibility_key": key, "endpoint_status": "ENDPOINT_COMPATIBLE",
                  "usage": preflight_report, "cache_hit": False, "model_call_performed": True}
        gate = "preflight/persistent/gate/"
        gate_result = ({**result, "identity": {}} if mode == "erased_labels" else result)
        put(out, gate + "gate-report.json", {"accepted": True, "results": [{"result": gate_result}]})
        independent = gate + "compiled-form-grounding/"
        put(out, independent + "preflight-result.json", result)
        cache = {**result, "observed_at_unix_ns": 1}
        if mode == "cache_mismatch":
            cache["identity"] = {**identity, "cli_executable_sha256": "e" * 64}
        put(out, "preflight/persistent/fresh-cache/" + key + ".json", cache)
        argv = [r"C:\another\codex.exe" if mode == "argv_mismatch" else exe, "exec",
                "--model", "different" if mode == "exec_wrong_model" else "gpt-5.6-luna",
                "-c", 'model_reasoning_effort="high"' if mode == "exec_wrong_effort" else 'model_reasoning_effort="low"',
                "-c", 'model_instructions_file="fixture.txt"', "-c", "project_doc_max_bytes=0",
                "-C", windows_root + r"\workspaces\persistent"]
        if mode == "exec_image":
            argv += ["--image", "fixture.png"]
        plan = {"args": argv + ["-"], "mode": "handle", "image_sha256": None}
        plan.update({field: identity[field] for field in
                     ("requested_model", "requested_effort", "runner_sha256", "schema_sha256",
                      "instructions_sha256")})
        put(out, independent + "model-call/plan.json", plan)
        put(out, independent + "model-call/process.json", {"exit_code": 0})
        events = [{"type": "thread.started", "thread_id": "preflight"},
                  {"type": "turn.started"}, {"type": "turn.completed", "usage": raw_preflight}]
        if mode == "failed_preflight":
            events.insert(2, {"type": "turn.failed", "error": {"message": "synthetic failure"}})
        if mode == "double_preflight_start":
            events.insert(2, {"type": "turn.started"})
        put(out, independent + "model-call/events.jsonl", events)
        runtime = "arms/persistent/runtime/"
        put(out, runtime + "submission-history.jsonl",
            [{"task_id": "task-" + str(index), "exact": True} for index in range(1, 7)])
        put(out, runtime + "events.jsonl", [
            {"event": "terminal", "release": {"verified": True, "keys_down": [], "buttons_down": []}},
            {"event": "target_handle_checked", "handle": "persistent_a_field",
             "status": "MISSING", "eligible": False},
        ])
        images = {}
        details = [{"trace": task, "source": {}} for task in report["tasks"]]
        for offset, stage in ((0, "anchor"), (3, "repair")):
            task = report["tasks"][offset]
            [call] = task["model_calls"]
            filename = f"{offset + 1:03}.png"
            original = wsl_root + "/" + runtime + filename
            provider_root = r"C:\different" if mode == "relocated_provider_root" else windows_root
            mounted = provider_root + "\\" + (runtime + filename).replace("/", "\\")
            if mode == "unc_case_substitution" and offset == 0:
                mounted = mounted.removesuffix(".png") + ".PNG"
            images[call["call_id"]] = mounted
            details[offset]["source"]["image"] = original
            content = f"synthetic observation {offset}".encode()
            (out / runtime / filename).write_bytes(
                b"modified image bytes" if mode == "changed_image_bytes" else content)
            prefix = f"model-calls/persistent/{task['task_id']}/{stage}/"
            put(out, prefix + "request.json", {"source_image": original, "provider_image": mounted,
                "image_sha256": hashlib.sha256(content).hexdigest()})
            persisted = PARTIAL if mode == "zero_edited_journal_and_ledger" and offset == 0 else raw_grounding[int(offset == 3)]
            provider = PARTIAL if mode == "result_usage_zero_only" and offset == 0 else persisted
            put(out, prefix + "result.json", {"thread_id": "thread", "call_id": call["call_id"],
                                            "turn_status": "completed", "raw": ANSWER,
                                            "usage": persisted, "provider_usage": provider_usage(provider)})
        (out / "arms/persistent/task-details.json").write_text(json.dumps(details), encoding="utf-8")
        if mode == "missing_protocol":
            return
        thread = {"method": "thread/start", "id": 7,
                  "params": {"model": "other" if mode == "thread_wrong_model" else "gpt-5.6-luna",
                             "config": {"model_reasoning_effort": "low"}}}
        rows = [{"direction": "send_prepared", "message": thread},
                {"direction": "sent", "message": thread},
                {"direction": "received", "message": {"id": 7, "result": {
                    "thread": {"id": "thread"}, "model": "gpt-5.6-luna",
                    "reasoningEffort": "high" if mode == "thread_wrong_effort" else "low"}}}]
        for index, usage in enumerate(raw_grounding, 1):
            turn = "turn-" + str(index)
            inputs = [{"type": "text", "text": "fixture"}]
            if mode != "turn_missing_image":
                sent_image = r"C:\unrelated.png" if mode == "same_unrelated_images" else images[turn]
                inputs.append({"type": "localImage", "path": sent_image})
            request = {"method": "turn/start", "id": index, "params": {
                "threadId": "thread", "model": "other" if mode == "turn_wrong_model" else "gpt-5.6-luna",
                "effort": "high" if mode == "turn_wrong_effort" else "low", "input": inputs}}
            phase = [
                {"direction": "send_prepared", "message": request},
                {"direction": "sent", "message": request},
                {"direction": "received", "message": {"id": index, "result": {"turn": {"id": turn}}}},
                {"direction": "received", "message": {"method": "thread/tokenUsage/updated",
                    "params": {"threadId": "thread", "turnId": turn, "tokenUsage": provider_usage(usage)}}},
                {"direction": "received", "message": {"method": "turn/completed",
                    "params": {"threadId": "thread", "turn": {"id": turn, "status": "completed",
                        "error": "fixture error" if mode == "completion_error" else None,
                        "items": ([] if mode == "completion_empty_items" else [
                            {"type": "agentMessage", "text": json.dumps(ANSWER)}])}}}},
            ]
            if index == 1:
                early = {"ack_before_sent": 2, "usage_before_sent": 3, "completion_before_sent": 4}
                if mode in early:
                    phase.insert(1, phase.pop(early[mode]))
                if mode == "late_usage":
                    phase.append(phase[3])
            rows.extend(phase)
        if mode == "second_completed_first":
            first_end = next(index for index, row in enumerate(rows)
                             if row["message"].get("method") == "turn/completed")
            rows.append(rows.pop(first_end))
        if mode == "extra_prepared":
            rows.append({"direction": "send_prepared", "message": {
                "method": "turn/start", "id": 3, "params": {"threadId": "thread"}}})
        put(out, "persistent-grounding-app-server/protocol.jsonl", rows)


if __name__ == "__main__":
    unittest.main()
