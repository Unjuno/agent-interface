"""Offline coverage of the explicit Windows executable preview bridge."""
import io
import json
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from runtime import golden_desktop_demo_v2 as demo

from codex_app_server_client_v2 import AppServerError, wsl_codex_home_environment
from integrated_efficiency_app_server_model_v1 import (
    GroundingCallError, PersistentGroundingModel,
)
import integrated_efficiency_model_v1 as legacy_model
import schema_preflight_v1 as preflight
import schema_preflight_gate_v1 as gate
import target_handle_model_runner_v2 as runner


USAGE = {"input_tokens": 8, "cached_input_tokens": 2, "cache_write_input_tokens": 0,
         "output_tokens": 3, "reasoning_output_tokens": 1}
WSL = {"WSL_INTEROP": "/run/WSL/mock", "CODEX_HOME": "/mnt/c/isolated",
       "WSLENV": "OTHER/w:CODEX_HOME/u:CODEX_HOME/l"}


class NativeCodexPreviewTests(unittest.TestCase):
    def test_opt_in_doctor_probes_only_selected_executable(self):
        base = demo.base
        display = ModuleType("Xlib.display")
        display.Display = Mock()
        with TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            executable = root / "Codex Folder" / "codex.exe"
            executable.parent.mkdir()
            executable.touch()
            completed = subprocess.CompletedProcess([], 0, "codex-cli test\n", "")
            with patch.dict(os.environ, {**WSL, "AGENT_INTERFACE_WINDOWS_CODEX_EXE": str(executable),
                                        "DISPLAY": ":fake"}, clear=True), \
                 patch.dict(sys.modules, {"Xlib": ModuleType("Xlib"), "Xlib.display": display}), \
                 patch.object(base.importlib.util, "find_spec", return_value=object()), \
                 patch("codex_app_server_client_v2.wsl_codex_home_environment",
                       return_value={"CODEX_HOME": str(root), "WSLENV": "CODEX_HOME/p"}), \
                 patch.object(base.subprocess, "run", return_value=completed) as run, \
                 patch.object(base, "windows_arg", return_value=r"C:\Codex Folder\codex.exe"):
                report = base.doctor()
            self.assertEqual(report["configuration"]["windows_codex_exe"], str(executable))
            self.assertNotIn("windows_node", report["configuration"])
            self.assertNotIn("windows_cli", report["configuration"])
            self.assertTrue(next(check["passed"] for check in report["checks"]
                                 if check["name"] == "codex_cli"))
            self.assertEqual(run.call_args.args[0], [str(executable), "--version"])
            self.assertEqual(report["native_codex"], {
                "windows_path": r"C:\Codex Folder\codex.exe", "version": "codex-cli test",
                "executable_sha256": base.sha(executable)})

    def test_broken_linux_browser_stops_before_preflight(self):
        base = demo.base
        display = ModuleType("Xlib.display")
        display.Display = Mock()
        with TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            exe, python, chrome = (root / name for name in ("codex.exe", "python.exe", "chrome-wrapper"))
            for path in (exe, python, chrome):
                path.touch()
            environment = {**WSL, "AGENT_INTERFACE_WINDOWS_CODEX_EXE": str(exe),
                           "AGENT_INTERFACE_WINDOWS_PYTHON": str(python),
                           "AGENT_INTERFACE_CHROMIUM": str(chrome), "DISPLAY": ":fake"}

            def version(argv, **options):
                if argv[0] == str(chrome):
                    self.assertEqual(options["timeout"], 10)
                    return subprocess.CompletedProcess(argv, 127, "", "libX11.so missing")
                return subprocess.CompletedProcess(argv, 0, "codex-cli test", "")

            with patch.dict(os.environ, environment, clear=True), \
                 patch.dict(sys.modules, {"Xlib": ModuleType("Xlib"), "Xlib.display": display}), \
                 patch.object(base.importlib.util, "find_spec", return_value=object()), \
                 patch.object(base.platform, "system", return_value="Linux"), \
                 patch.object(base.platform, "platform", return_value="Linux fixture"), \
                 patch.object(base.shutil, "which", return_value="/usr/bin/wslpath"), \
                 patch.object(base.os, "access", return_value=True), \
                 patch("codex_app_server_client_v2.wsl_codex_home_environment",
                       return_value={"CODEX_HOME": str(root)}), \
                 patch.object(base.subprocess, "run", side_effect=version), \
                 patch.object(base, "configure_research_modules") as configure:
                report = base.doctor()
                self.assertEqual([check["name"] for check in report["checks"] if not check["passed"]],
                                 ["chromium"])
                with self.assertRaisesRegex(RuntimeError, "doctor failed"):
                    demo.run_live(root / "out", 123)
            configure.assert_not_called()
            self.assertFalse((root / "out").exists())

    def test_chromium_launcher_accepts_linux_wrapper_and_rejects_windows_exe(self):
        base = demo.base
        with TemporaryDirectory() as directory:
            root = Path(directory)
            wrapper, exe = root / "google-chrome", root / "chrome.exe"
            wrapper.touch()
            exe.touch()
            healthy = subprocess.CompletedProcess([], 0, "Google Chrome 147.0.0\n", "")
            with patch.object(base.platform, "system", return_value="Linux"), \
                 patch.object(base.os, "access", return_value=True), \
                 patch.object(base.subprocess, "run", return_value=healthy) as run:
                self.assertEqual(base.chromium_version(wrapper), "Google Chrome 147.0.0")
                with self.assertRaisesRegex(ValueError, "executable Linux"):
                    base.chromium_version(exe)
            self.assertEqual(run.call_count, 1)

    def test_main_preserves_existing_output_and_records_only_owned_failure(self):
        base = demo.base
        for reuse in (False, True):
            with self.subTest(reuse=reuse), TemporaryDirectory() as directory:
                out = Path(directory) / "out"
                failure = out / "failure.json"
                if reuse:
                    out.mkdir()
                    failure.write_bytes(b"original owner evidence")
                with patch.object(base, "run_live", demo.run_live), \
                     patch.object(base, "doctor", return_value={"passed": True}), \
                     patch.object(base, "configuration", side_effect=RuntimeError("synthetic error")), \
                     patch.object(sys, "argv", ["golden", "run", "--out", str(out)]), \
                     patch.object(sys, "stderr", new_callable=io.StringIO) as errors:
                    self.assertEqual(base.main(), 2)
                reported = json.loads(errors.getvalue())
                if reuse:
                    self.assertEqual(failure.read_bytes(), b"original owner evidence")
                    self.assertIsNone(reported["output_retained"])
                else:
                    self.assertEqual(json.loads(failure.read_bytes()), reported)
                    self.assertEqual(reported["error_type"], "RuntimeError")

    def test_configuration_selects_native_for_the_same_schema_preflight_module(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            selected = root / "codex.exe"
            python = root / "python.exe"
            config = {"windows_python": python, "windows_codex_exe": selected}
            linux_modules = {
                "integrated_efficiency_client_v1": SimpleNamespace(RuntimeClient=object),
                "run_integrated_efficiency_live_v1": SimpleNamespace(),
            }
            with patch.dict(sys.modules, linux_modules), \
                 patch.object(preflight, "CLI_EXE_WSL", None), \
                 patch.object(preflight, "WINDOWS_PYTHON", None), \
                 patch.object(legacy_model, "WINDOWS_PYTHON", None):
                demo.base.configure_research_modules(config, root / "chrome")
                self.assertIs(gate.preflight.__globals__, preflight.__dict__)
                self.assertEqual(preflight.CLI_EXE_WSL, selected)
                self.assertEqual(preflight.WINDOWS_PYTHON, python)

    def test_wsl_environment_uses_native_path_translation_once(self):
        self.assertEqual(wsl_codex_home_environment(WSL)["WSLENV"], "OTHER/w:CODEX_HOME/p")
        self.assertEqual(WSL["WSLENV"], "OTHER/w:CODEX_HOME/u:CODEX_HOME/l")
        for env in ({}, {**WSL, "CODEX_HOME": "relative"}):
            with self.subTest(env=env), self.assertRaises(AppServerError):
                wsl_codex_home_environment(env)

    def test_native_schema_gate_separates_binary_cache_and_only_allows_optional_field_omission(self):
        modes = ("complete", "partial", "missing_required", "invalid", "mixed_terminal",
                 "double_start", "missing_job", "outer_timeout")
        for mode in modes:
            with self.subTest(mode=mode), TemporaryDirectory() as directory:
                root = Path(directory)
                executable = root / "Codex Folder" / "codex.exe"
                executable.parent.mkdir()
                executable.write_bytes(b"candidate")
                schema = root / "schema.json"
                schema.write_text('{"type":"object"}', encoding="utf-8")
                cli_js = root / "codex.js"
                cli_js.write_bytes(b"legacy")
                workspace = root / "workspace"
                workspace.mkdir()
                gate_dir = root / "gate"
                called_argv = []

                def fake_run(argv, **options):
                    if argv[-1] == "--version":
                        return subprocess.CompletedProcess(argv, 0, "codex-cli test\n", "")
                    called_argv.append(argv)
                    self.assertEqual(options["env"]["WSLENV"], "OTHER/w:CODEX_HOME/p")
                    if mode == "outer_timeout":
                        raise subprocess.TimeoutExpired(argv, 90)
                    evidence = gate_dir / "compiled"
                    if mode != "missing_job":
                        owner_start = json.loads((evidence / "windows-job-start.json").read_bytes())
                        ownership = {**owner_start, "schema": "native-preflight-windows-job-v1",
                                     "ownership": "create-process-job-list", "status": "COMPLETED",
                                     "exit_code": 0, "job_empty": True, "active_processes": 0,
                                     "total_processes": 2}
                        (evidence / "windows-job.json").write_text(json.dumps(ownership), encoding="utf-8")
                    events = evidence / "model-call" / "events.jsonl"
                    events.parent.mkdir()
                    usage = dict(USAGE)
                    if mode == "partial":
                        del usage["cache_write_input_tokens"]
                    elif mode == "missing_required":
                        del usage["output_tokens"]
                    elif mode == "invalid":
                        usage["cache_write_input_tokens"] = None
                    rows = [{"type": "thread.started", "thread_id": "preflight"},
                            {"type": "turn.started"}, {"type": "turn.completed", "usage": usage}]
                    if mode == "mixed_terminal":
                        rows.insert(2, {"type": "turn.failed", "error": {"message": "synthetic"}})
                    if mode == "double_start":
                        rows.insert(2, {"type": "turn.started"})
                    events.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
                    return subprocess.CompletedProcess(argv, 0, b"", b"")

                with patch.dict(os.environ, WSL, clear=True), \
                     patch.object(preflight, "CLI_WSL", cli_js), \
                     patch.object(preflight, "CLI_EXE_WSL", None), \
                     patch.object(preflight, "windows_path", side_effect=lambda p: "W:" + str(p)), \
                     patch.object(preflight.subprocess, "run", side_effect=fake_run):
                    old_identity, old_key = preflight.compatibility_identity(schema)
                    preflight.CLI_EXE_WSL = executable
                    new_identity, new_key = preflight.compatibility_identity(schema)
                    if mode not in ("complete", "partial"):
                        with self.assertRaises(gate.SchemaPreflightRefused) as stopped:
                            gate.require_compatible([{"name": "compiled", "schema": schema}],
                                                    root / "cache", gate_dir, workspace)
                        report = stopped.exception.report
                    else:
                        report = gate.require_compatible([{"name": "compiled", "schema": schema}],
                                                         root / "cache", gate_dir, workspace)
                self.assertNotIn("node_version", new_identity)
                self.assertIn("node_version", old_identity)
                self.assertNotEqual(old_key, new_key)
                self.assertEqual(new_identity["cli_executable_sha256"],
                                 preflight.sha(executable))
                argv, = called_argv
                self.assertTrue(argv[1].endswith("native_preflight_job_v1.py"))
                self.assertEqual(argv[5:7], ["--native-codex-exe", "W:" + str(executable)])
                self.assertEqual(argv[10:12], ["handle", "-"])
                result = report["results"][0]["result"]
                self.assertEqual(result["compatibility_key"], new_key)
                self.assertEqual(report["accepted"], mode in ("complete", "partial"))
                if mode == "complete":
                    self.assertEqual(result["usage"], USAGE)
                    self.assertEqual(result["usage_status"], "complete")
                elif mode == "partial":
                    self.assertEqual(result["usage"],
                                     {field: value for field, value in USAGE.items()
                                      if field != "cache_write_input_tokens"})
                    self.assertEqual(result["usage_status"], "partial")
                else:
                    self.assertIsNone(result["usage"])
                    status = {"mixed_terminal": "ENDPOINT_INCOMPATIBLE",
                              "double_start": "PREFLIGHT_LIFECYCLE_UNVERIFIED",
                              "missing_job": "PREFLIGHT_JOB_UNVERIFIED",
                              "outer_timeout": "PREFLIGHT_JOB_UNVERIFIED"}.get(
                                  mode, "PREFLIGHT_USAGE_UNVERIFIED")
                    self.assertEqual(result["endpoint_status"], status)
                    if status == "PREFLIGHT_JOB_UNVERIFIED":
                        self.assertIsNone(report["model_calls"])
                        self.assertIsNone(result["model_call_performed"])

    def test_native_refuses_an_override_runner_before_launch(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            touched = root / "custom.py"
            touched.write_text("custom", encoding="utf-8")
            with patch.object(preflight, "RUNNER", touched), \
                 patch.object(preflight, "CLI_EXE_WSL", root / "codex.exe"), \
                 patch.object(preflight.subprocess, "run") as run:
                with self.assertRaisesRegex(ValueError, "built-in"):
                    preflight.compatibility_identity(touched)
            run.assert_not_called()

    def test_windows_runner_replaces_only_exec_prefix_in_native_mode(self):
        with TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            executable = root / "Codex Folder" / "codex.exe"
            prompt, instructions, schema = (root / name for name in ("prompt", "instructions", "schema"))
            for path in (prompt, instructions, schema):
                path.write_text("synthetic", encoding="utf-8")
            argv = []
            for prefix in (["node.exe", "codex.js"], ["--native-codex-exe", str(executable)]):
                output = root / str(len(argv))
                fake = SimpleNamespace(stdin=io.BytesIO(), stdout=io.BytesIO(), wait=lambda: 0)
                with patch.object(sys, "argv", ["runner.py", *prefix, str(prompt), str(root),
                                               str(output), "handle", "-", str(instructions), str(schema)]), \
                     patch.object(runner.subprocess, "Popen", return_value=fake) as launch, \
                     patch("builtins.print"):
                    self.assertEqual(runner.main(), 0)
                argv.append(launch.call_args.args[0])
            self.assertEqual(argv[0][:2], ["node.exe", "codex.js"])
            self.assertEqual(argv[1][0], str(executable))
            self.assertEqual(argv[1][1:], argv[0][2:])
            self.assertIn("--ignore-user-config", argv[1])
            self.assertIn("--ignore-rules", argv[1])
            self.assertIn("read-only", argv[1])

    def test_failed_grounding_paths_refuse_inconsistent_known_usage(self):
        usage = {"last": {"inputTokens": 8, "cachedInputTokens": 2,
                          "cacheWriteInputTokens": 0, "outputTokens": 3,
                          "reasoningOutputTokens": 4}}
        for await_error in (False, True):
            with self.subTest(await_error=await_error), TemporaryDirectory() as directory:
                root = Path(directory)
                client = Mock()
                client.start_thread.return_value = {"thread": {"id": "thread"}}
                client.start_turn.return_value = {"turn": {"id": "turn"}}
                client.latest_turn_usage.return_value = usage
                model = PersistentGroundingModel(root / "session", root, client=client,
                                                 path_converter=str, require_complete_usage=True)
                returned = SimpleNamespace(answer_eligible=False, usage=usage, status="failed",
                                           error="synthetic rejected answer")
                with patch.object(model.planner, "await_turn", return_value=returned,
                                  side_effect=TimeoutError("synthetic timeout") if await_error else None):
                    with self.assertRaises(GroundingCallError) as stopped:
                        model.call(root / "call", "fixture", root / "image", "compiled", root)
                self.assertEqual(stopped.exception.call_id, "turn")
                self.assertIsNone(stopped.exception.usage)
                self.assertIn("inconsistent", stopped.exception.usage_error)
                self.assertEqual(client.start_turn.call_count, 1)

    def test_owned_native_client_is_closed_when_startup_fails(self):
        for phase in ("initialize", "path", "thread"):
            with self.subTest(phase=phase), TemporaryDirectory() as directory:
                root = Path(directory)
                client = Mock()
                client.start_thread.return_value = {"thread": {"id": "thread"}}
                error = RuntimeError("synthetic " + phase)
                convert = Mock(side_effect=error if phase == "path" else str)
                if phase == "initialize":
                    client.initialize.side_effect = error
                if phase == "thread":
                    client.start_thread.side_effect = error
                with patch("integrated_efficiency_app_server_model_v1.CodexAppServerClient",
                           return_value=client):
                    with self.assertRaisesRegex(RuntimeError, "synthetic " + phase):
                        PersistentGroundingModel(root / "session", root, executable=root / "codex.exe",
                                                 path_converter=convert)
                client.close.assert_called_once()

    def test_strict_grounding_rejects_missing_usage_without_retry(self):
        incomplete = {"last": {"inputTokens": 8, "cachedInputTokens": 2,
                               "outputTokens": 3, "reasoningOutputTokens": 1}}
        for usage in (None, incomplete):
            with self.subTest(usage=usage), TemporaryDirectory() as directory:
                root = Path(directory)
                client = Mock()
                client.start_thread.return_value = {"thread": {"id": "thread"}}
                client.start_turn.return_value = {"turn": {"id": "turn"}}
                model = PersistentGroundingModel(root / "session", root, client=client,
                                                 path_converter=str, require_complete_usage=True)
                returned = SimpleNamespace(answer_eligible=True, usage=usage)
                with patch.object(model.planner, "await_turn", return_value=returned):
                    with self.assertRaises(GroundingCallError) as stopped:
                        model.call(root / "call", "fixture", root / "image", "compiled", root)
                self.assertEqual(stopped.exception.call_id, "turn")
                self.assertIsNone(stopped.exception.usage)
                self.assertEqual(client.start_turn.call_count, 1)


if __name__ == "__main__":
    unittest.main()
