"""Exercise registration, claim, worker and audit without GUI or provider calls."""

from contextlib import contextmanager, nullcontext, redirect_stdout
import io
import json
import os
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from research.live_control import native_comparison_arm_x11_v1 as x11
from runtime import native_comparison_cli_v1 as cli
from runtime.test_native_comparison_audit_v1 import SyntheticCapture


def complete_capture():
    return {"schema": "native_comparison_capture_v1", "disposition": "HOLD",
            "reason": "independent_raw_audit_required", "arms": dict.fromkeys(cli.audit.ARMS, "captured")}


def persistent_incomplete_capture():
    result = complete_capture()
    result["reason"] = "task_or_independent_effect_incomplete"
    result["arms"]["persistent"] = "incomplete"
    return result


def service_proof(unit):
    uid = os.getuid()
    return {"KillMode": "control-group", "RuntimeMaxUSec": "30min", "TimeoutStopUSec": "8s", "MainPID": "110",
            "ControlGroup": f"/user.slice/user-{uid}.slice/user@{uid}.service/app.slice/{unit}"}


def display_proof(service, *, number=120, pid=201, arm=None, started=100):
    truth = {
        "scope": "actual_comparison_arm_display" if arm is not None else "supervisor_doctor_display",
        "display": f":{number}", "number": number, "pids": [pid, pid + 1],
        "lock": f"/tmp/.X{number}-lock", "lock_pid": pid, "xauthority": f"/tmp/fixture-{pid}/Xauthority",
        "xauthority_mode": "0600", "xauthority_uid": os.getuid(), "service_unit": service["unit"],
        "claim_token": service["claim_token"], "service_group": service["ControlGroup"],
        "input_neutral": True, "xtest": True, "wayland_present": False,
    }
    if arm is not None:
        truth.update(arm=arm, started_monotonic_ns=started)
    return truth


def retire(proof):
    record = {**proof, "retired": True, "lock_absent": True, "owned_returncodes": [0, 0]}
    if "arm" in proof:
        record.update(input_neutral_at_end=True, finished_monotonic_ns=proof["started_monotonic_ns"] + 40)
    return record


def add_arm_proofs(allocation, service):
    for index, arm in enumerate(cli.audit.ARMS, start=1):
        runtime = allocation / "raw" / "arms" / arm / "runtime"
        runtime.mkdir(parents=True)
        begin = index * 1000
        proof = display_proof(service, number=121, pid=300 + 10 * index, arm=arm, started=begin + 10)
        cli.audit.write_record(runtime / "comparison-display-start.json", proof)
        cli.audit.write_record(runtime / "comparison-display-end.json", retire(proof))
        events = [{"event": "ready", "emit_started_ns": begin + 20}, {"event": "terminal", "terminal_ns": begin + 30}]
        (runtime / "events.jsonl").write_text("".join(json.dumps(event) + "\n" for event in events))
        receipts = allocation / "raw" / "capture-arms" / arm
        receipts.mkdir(parents=True)
        cli.audit.write_record(receipts / "arm-timing.json",
                               {"arm_started_ns": begin, "arm_finished_ns": begin + 60})


@unittest.skipUnless(os.name == "posix", "launches the WSL/POSIX entrypoint")
class NativeComparisonCliTests(unittest.TestCase):
    def source_and_host(self, root):
        config = {}
        for name in cli.VARIABLES:
            path = root / name
            path.touch()
            config[name] = str(path)
        host = {"native": {"executable_sha256": "1" * 64, "version": "codex-cli dummy"},
                "linux_python": {"path": "/dummy/python", "version": "3.12"}}
        source = {"revision": "dummy checkout", "files": {}}
        return config, host, source

    def test_cli_one_shot_dry_end_to_end(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            allocation = root / "allocation"
            config, host, source = self.source_and_host(root)
            actions = []
            seal = "d" * 64

            def register(repo, out, seed, **host_data):
                self.assertEqual(out, allocation / "raw")
                self.assertEqual(seed, 654321)
                return {"source": source}

            @contextmanager
            def display(allocated, service):
                self.assertEqual(allocated, allocation)
                self.assertTrue(service["ControlGroup"].endswith(".service"))
                actions.append("own-dummy-display")
                proof = display_proof(service)
                cli.audit.write_record(allocation / "display-start.json", proof)
                yield
                actions.append("retire-dummy-display")
                cli.audit.write_record(allocation / "display-end.json", retire(proof))

            def capture(repo, out, registration, *, registration_sha256):
                self.assertEqual(registration_sha256, cli.audit.digest(registration))
                out.mkdir()
                add_arm_proofs(allocation, cli.audit.read(allocation / "service-start.json"))
                result = complete_capture()
                cli.audit.write_record(out / "capture.json", result)
                actions.append("capture-dummy")
                return {"capture": result}

            def launch(command, **kwargs):
                claim = cli.audit.read(allocation / "claim.json")
                self.assertIn("--property=KillMode=control-group", command)
                self.assertIn("--setenv=WSL_INTEROP", command)
                self.assertIn("--unit=" + claim["unit"], command)
                self.assertEqual(command[-4], "_service")
                actions.append("launch-dummy")
                with patch.dict(os.environ), patch.object(cli, "effective_service",
                        return_value=service_proof(claim["unit"])):
                    exit_code = cli.run_service(*command[-3:])
                return subprocess.CompletedProcess(command, exit_code)

            def judge(repo, out, registration, *, registration_sha256, seal_sha256):
                self.assertEqual(registration_sha256, cli.audit.digest(registration))
                self.assertEqual(seal_sha256, seal)
                actions.append("audit-dummy")
                return {"disposition": "RETAIN"}

            with patch.object(cli, "host_inputs", return_value=host), \
                 patch.object(cli, "windows_path", return_value=r"C:\dummy"), \
                 patch.object(cli.audit, "registration_values", side_effect=register), \
                 patch.object(cli.audit, "source_snapshot", return_value=source), \
                 patch.object(cli, "exclusive_launch", side_effect=lambda role="caller": nullcontext()), \
                 patch.object(cli, "owned_display", display), \
                 patch.object(cli.audit, "capture_registered", side_effect=capture), \
                 patch.object(cli.audit, "seal_capture", return_value=seal), \
                 patch.object(cli.failure_evidence, "native_writers_retired", return_value=True), \
                 patch.object(cli, "failed_service_retired", return_value=True), \
                 patch.object(cli, "cgroup_retired", return_value=True), \
                 patch.object(cli.audit, "audit_comparison", side_effect=judge), \
                 patch.object(cli.subprocess, "run", side_effect=launch):
                args = [opt for name, value in config.items() for opt in ("--" + name.replace("_", "-"), value)]
                stdout = io.StringIO()
                with redirect_stdout(stdout):
                    self.assertEqual(cli.main(["prepare", str(allocation), "--seed", "654321", *args]), 0)
                digest = json.loads(stdout.getvalue())["launch_plan_sha256"]
                self.assertEqual(actions, [])
                with self.assertRaisesRegex(ValueError, "explicit"):
                    cli.run_once(allocation, digest, confirm_live=False)
                self.assertFalse((allocation / "claim.json").exists())
                outbound = io.StringIO()
                with redirect_stdout(outbound):
                    self.assertEqual(cli.main(["run", str(allocation), digest, "--confirm-live"]), 0)
                result = json.loads(outbound.getvalue())
                host_digest = cli.audit.digest(allocation / "host-seal.json")
                self.assertEqual(result, {"disposition": "RETAIN", "seal_sha256": seal,
                                          "host_seal_sha256": host_digest})
                self.assertEqual(actions, ["launch-dummy", "own-dummy-display", "capture-dummy",
                                           "retire-dummy-display", "audit-dummy"])
                with self.assertRaisesRegex(ValueError, "already been claimed"):
                    cli.run_once(allocation, digest, confirm_live=True)
                self.assertEqual(actions.count("launch-dummy"), 1)
                self.assertEqual(cli.adjudicate(allocation, digest, expected_seal="e" * 64,
                                               expected_host_seal=host_digest)["disposition"], "HOLD")
                self.assertEqual(cli.adjudicate(allocation, digest, expected_seal=seal,
                                               expected_host_seal=host_digest)["disposition"], "RETAIN")
                self.assertEqual(actions.count("audit-dummy"), 2)
                service_path = allocation / "service-start.json"
                pristine = service_path.read_bytes()
                for field, value in (("KillMode", "process"), ("RuntimeMaxUSec", "infinity"),
                                     ("MainPID", "0"), ("claim_token", "0" * 32),
                                     ("ControlGroup", "/dummy/nonexistent")):
                    with self.subTest(host_receipt=field):
                        payload = cli.audit.read(service_path)
                        payload[field] = value
                        service_path.write_text(json.dumps(payload))
                        self.assertEqual(cli.adjudicate(allocation, digest, expected_seal=seal,
                            expected_host_seal=host_digest)["disposition"], "HOLD")
                        host_seal = allocation / "host-seal.json"
                        host_seal.write_text(json.dumps(cli.host_seal_values(allocation, digest)))
                        self.assertEqual(cli.adjudicate(allocation, digest, expected_seal=seal,
                            expected_host_seal=cli.audit.digest(host_seal))["disposition"], "HOLD")
                        service_path.write_bytes(pristine)
                host_seal.write_text(json.dumps(cli.host_seal_values(allocation, digest)))
                (allocation / "raw/arms/ephemeral/runtime/comparison-display-end.json").unlink()
                self.assertEqual(cli.adjudicate(allocation, digest, expected_seal=seal,
                    expected_host_seal=cli.audit.digest(host_seal))["disposition"], "HOLD")
                self.assertEqual(actions.count("audit-dummy"), 2)

    def test_modified_preregistration_stops_before_claim_and_service(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            allocation = root / "allocation"
            config, host, source = self.source_and_host(root)
            with patch.object(cli, "host_inputs", return_value=host), \
                 patch.object(cli, "windows_path", return_value=r"C:\dummy"), \
                 patch.object(cli.audit, "registration_values", return_value={"source": source}):
                plan = cli.prepare(allocation, 2, config)
            with (allocation / "registration.json").open("a", encoding="utf8") as stream:
                stream.write("\n")
            with patch.object(cli.subprocess, "run") as launch:
                with self.assertRaisesRegex(ValueError, "registration"):
                    cli.run_once(allocation, plan["launch_plan_sha256"], confirm_live=True)
            self.assertFalse((allocation / "claim.json").exists())
            launch.assert_not_called()

    def test_failed_unit_seals_available_evidence_and_refuses_later_changes(self):
        for failure in ("partial", "seal_write", "still_alive", "before_raw", "transport_timeout",
                        "windows_unsettled", "windows_retired"):
            with self.subTest(failure=failure), TemporaryDirectory() as directory:
                root = Path(directory)
                allocation = root / "allocation"
                config, host, source = self.source_and_host(root)
                with patch.object(cli, "host_inputs", return_value=host), \
                     patch.object(cli, "windows_path", return_value=r"C:\dummy"), \
                     patch.object(cli.audit, "registration_values", return_value={"source": source}):
                    plan = cli.prepare(allocation, 2, config)
                digest = plan["launch_plan_sha256"]
                available = allocation / "raw" / "capture-plan.json"
                first = cli.audit.write_record
                secret = root / "unrelated"
                secret.write_text("must never be hashed", encoding="utf-8")

                def failed(command, **kwargs):
                    if command[:3] == ["systemctl", "--user", "stop"]:
                        self.assertEqual(command[3], cli.audit.read(allocation / "claim.json")["unit"])
                        return subprocess.CompletedProcess(command, 0)
                    if failure != "before_raw":
                        available.parent.mkdir()
                        available.write_text('{"partly_observed": true}\n', encoding="utf-8")
                        if failure == "partial":
                            (available.parent / "unexpected-link").symlink_to(secret)
                        if failure in {"windows_unsettled", "windows_retired"}:
                            folder = available.parent / "preflight/plain/gate/plain-form-grounding"
                            folder.mkdir(parents=True)
                            reference = {"run_nonce": "a" * 32, "owner_sha256": "b" * 64}
                            first(folder / cli.audit.START_RECORD, reference)
                            if failure == "windows_retired":
                                first(folder / cli.audit.RECEIPT, {**reference,
                                    "schema": "native-preflight-windows-job-v1",
                                    "ownership": "create-process-job-list", "status": "OWNER_LOST",
                                    "job_empty": True, "active_processes": 0, "total_processes": 2,
                                    "exit_code": 124})
                    if failure == "transport_timeout":
                        raise subprocess.TimeoutExpired(command, timeout=1)
                    return subprocess.CompletedProcess(command, 17)

                def write(path, value):
                    if failure == "seal_write" and path.name == "partial-raw-seal.json":
                        raise OSError("synthetic raw seal write failure")
                    return first(path, value)

                with patch.object(cli, "host_inputs", return_value=host), \
                     patch.object(cli.audit, "source_snapshot", return_value=source), \
                     patch.object(cli, "exclusive_launch", side_effect=lambda role="caller": nullcontext()), \
                     patch.object(cli, "failed_service_retired", return_value=failure != "still_alive", create=True), \
                     patch.object(cli.audit, "write_record", side_effect=write), \
                     patch.object(cli.subprocess, "run", side_effect=failed) as launch:
                    result = cli.run_once(allocation, digest, confirm_live=True)
                    self.assertEqual(result["disposition"], "HOLD")
                    worker = cli.audit.read(allocation / "service-result.json")
                    self.assertEqual(worker["returncode"], None if failure == "transport_timeout" else 17)
                    if failure == "transport_timeout":
                        self.assertEqual(worker["stop_returncode"], 0)
                    with self.assertRaisesRegex(ValueError, "already been claimed"):
                        cli.run_once(allocation, digest, confirm_live=True)
                    self.assertEqual(launch.call_count, 2 if failure == "transport_timeout" else 1)
                self.assertIn("host_seal_sha256", result)
                if failure == "seal_write":
                    self.assertNotIn("seal_sha256", result)
                    self.assertEqual(result["preservation"]["raw"]["status"], "failed")
                    self.assertIn("synthetic raw seal write failure", result["preservation"]["raw"]["reason"])
                    verified_host = cli.adjudicate(allocation, digest,
                                                   expected_host_seal=result["host_seal_sha256"])
                    self.assertEqual(verified_host["disposition"], "HOLD")
                    self.assertIs(verified_host["host_manifest_verified"], True)
                    self.assertIs(verified_host["partial_manifests_verified"], False)
                    continue
                raw = cli.audit.read(allocation / "partial-raw-seal.json")
                hosts = cli.audit.read(allocation / "partial-host-seal.json")
                self.assertIn("display-end.json", hosts["snapshot"]["missing"] if failure != "still_alive"
                              else hosts["snapshot"]["unsealed"])
                if failure == "still_alive":
                    self.assertEqual(raw["snapshot"]["state"], "unsettled")
                    self.assertEqual(raw["snapshot"]["files"], {})
                    continue
                if failure == "windows_unsettled":
                    self.assertEqual(raw["snapshot"]["state"], "unsettled")
                    self.assertEqual(raw["snapshot"]["files"], {})
                    self.assertEqual(raw["snapshot"]["unsealed"]["."], "windows_job_retirement_unverified")
                    self.assertIn("service-result.json", hosts["snapshot"]["files"])
                    continue
                if failure == "before_raw":
                    self.assertEqual(raw["snapshot"]["state"], "absent")
                    self.assertIn("capture-plan.json", raw["snapshot"]["missing"])
                    continue
                self.assertIn("capture-plan.json", raw["snapshot"]["files"])
                self.assertIn("capture.json", raw["snapshot"]["missing"])
                if failure == "partial":
                    self.assertEqual(raw["snapshot"]["unsealed"]["unexpected-link"], "non_regular_artifact")
                verified = cli.adjudicate(allocation, digest, expected_seal=result["seal_sha256"],
                    expected_host_seal=result["host_seal_sha256"])
                self.assertIs(verified["partial_manifests_verified"], True)
                host_log = allocation / "service.stderr"
                before = host_log.read_bytes()
                host_log.write_bytes(b"changed out of band\n")
                changed_host = cli.adjudicate(allocation, digest, expected_seal=result["seal_sha256"],
                    expected_host_seal=result["host_seal_sha256"])
                self.assertIn("changed after preservation", changed_host["reason"])
                host_log.write_bytes(before)
                available.write_text('{"changed": true}\n', encoding="utf-8")
                changed = cli.adjudicate(allocation, digest, expected_seal=result["seal_sha256"],
                    expected_host_seal=result["host_seal_sha256"])
                self.assertEqual(changed["disposition"], "HOLD")
                self.assertIn("changed after preservation", changed["reason"])

    def test_registered_capture_interrupted_after_native_start_has_no_full_seal(self):
        from runtime import golden_desktop_demo

        with TemporaryDirectory() as directory:
            root = Path(directory)
            out = root / "raw"
            registration = root / "registration.json"
            native = {"version": "codex-cli dummy"}
            plan = {"seed": 2, "native": native}
            cli.audit.write_record(registration, plan)

            def timeout(arm, contract, workspace):
                home = out / "preflight" / arm / "gate" / (contract + "-form-grounding")
                home.mkdir(parents=True)
                cli.audit.write_record(home / cli.audit.START_RECORD,
                                       {"run_nonce": "a" * 32, "owner_sha256": "b" * 64})
                raise TimeoutError("synthetic native owner did not return")

            bindings = {"preflight": timeout, "run_arm": None, "open_grounding": None}
            with patch.object(cli.audit, "registration_values", return_value=plan), \
                 patch.object(golden_desktop_demo, "windows_arg", return_value=r"C:\dummy"), \
                 patch.object(cli.audit, "bind_golden_runner", return_value=nullcontext(({"native_codex": native}, bindings))):
                result = cli.audit.capture_registered(cli.ROOT, out, registration,
                                                      registration_sha256=cli.audit.digest(registration))
            self.assertEqual(result["capture"]["arms"]["plain"], "interrupted")
            self.assertNotIn("seal_sha256", result)
            self.assertFalse((out / "capture-seal.json").exists())

    def test_missing_native_markers_are_unsettled_if_runtime_traces_exist(self):
        from runtime import native_comparison_failure_v1 as retained

        for kind in ("exec", "appserver"):
            with self.subTest(kind=kind), TemporaryDirectory() as directory:
                raw = Path(directory)
                self.assertTrue(retained.native_writers_retired(raw))
                if kind == "exec":
                    artifact = raw / "preflight/plain/gate/plain-form-grounding/model-call/events.jsonl"
                    event = {"type": "thread.started", "thread_id": "dummy"}
                else:
                    artifact = raw / "native-app-server/plain/protocol.jsonl"
                    event = {"direction": "windows_job_owner", "message": {"run_nonce": "a" * 32}}
                artifact.parent.mkdir(parents=True)
                artifact.write_text(json.dumps(event) + "\n", encoding="utf-8")
                self.assertFalse(retained.native_writers_retired(raw))

    def test_zero_exit_with_unsettled_native_writer_cannot_publish_full_seal(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            allocation = root / "allocation"
            config, host, source = self.source_and_host(root)
            with patch.object(cli, "host_inputs", return_value=host), \
                 patch.object(cli, "windows_path", return_value=r"C:\dummy"), \
                 patch.object(cli.audit, "registration_values", return_value={"source": source}):
                prepared = cli.prepare(allocation, 2, config)

            def exited_without_native_retirement(command, **kwargs):
                claim = cli.audit.read(allocation / "claim.json")
                raw = allocation / "raw"
                raw.mkdir()
                result = complete_capture()
                cli.audit.write_record(raw / "capture.json", result)
                cli.audit.write_record(allocation / "capture-worker-result.json", {
                    "unit": claim["unit"], "claim_token": claim["token"], "capture": result,
                })
                scope = raw / "native-app-server/plain"
                scope.mkdir(parents=True)
                cli.audit.write_record(scope / cli.audit.APP_SERVER_JOB_START, {
                    "run_nonce": "a" * 32, "owner_sha256": "b" * 64,
                })
                return subprocess.CompletedProcess(command, 0)

            with patch.object(cli, "host_inputs", return_value=host), \
                 patch.object(cli.audit, "source_snapshot", return_value=source), \
                 patch.object(cli, "exclusive_launch", side_effect=lambda role="caller": nullcontext()), \
                 patch.object(cli, "failed_service_retired", return_value=True), \
                 patch.object(cli.subprocess, "run", side_effect=exited_without_native_retirement), \
                 patch.object(cli.audit, "seal_capture") as full:
                result = cli.run_once(allocation, prepared["launch_plan_sha256"], confirm_live=True)
            full.assert_not_called()
            self.assertEqual(result["disposition"], "HOLD")
            self.assertEqual(result["preservation"]["raw"]["state"], "unsettled")
            self.assertFalse((allocation / "audit-anchor.json").exists())
            self.assertFalse((allocation / "raw/capture-seal.json").exists())

    def test_worker_reports_stop_when_capture_cannot_be_adjudicated(self):
        interruption = {**complete_capture(), "reason": "preflight_interrupted",
                        "arms": {"plain": "interrupted", "ephemeral": "not_run", "persistent": "not_run"}}
        reference_incomplete = {**persistent_incomplete_capture(),
                                "arms": {"plain": "incomplete", "ephemeral": "not_run", "persistent": "not_run"}}
        for result in (interruption, reference_incomplete):
            with self.subTest(result=result):
                self.check_worker_exit(result, 2)

    def test_worker_passes_closed_persistent_failure_to_adjudication(self):
        self.check_worker_exit(persistent_incomplete_capture(), 0)

    def check_worker_exit(self, result, expected_code):
        with TemporaryDirectory() as directory:
            allocation = Path(directory)
            settings, host, _ = self.source_and_host(allocation)
            token, digest = "a" * 32, "b" * 64
            unit = f"agent-interface-native-comparison-{token}.service"
            cli.audit.write_record(allocation / "claim.json", {
                "token": token, "unit": unit, "launch_plan_sha256": digest,
            })
            plan = {"settings": settings, "host": host, "registration_sha256": "c" * 64}

            @contextmanager
            def display(folder, service):
                cli.audit.write_record(folder / "display-start.json", display_proof(service))
                yield

            with patch.dict(os.environ), patch.object(cli, "load_plan",
                    return_value=(allocation, plan, allocation / "registration.json")), \
                 patch.object(cli, "effective_service", return_value=service_proof(unit)), \
                 patch.object(cli, "host_inputs", return_value=host), \
                 patch.object(cli, "exclusive_launch", side_effect=lambda role="caller": nullcontext()), \
                 patch.object(cli, "owned_display", display), \
                 patch.object(cli.audit, "capture_registered", return_value={"capture": result}), \
                 patch.object(cli.audit, "seal_capture") as full:
                self.assertEqual(cli.run_service(allocation, digest, token), expected_code)
            full.assert_not_called()
            self.assertFalse((allocation / "audit-anchor.json").exists())
            self.assertEqual(cli.audit.read(allocation / "capture-worker-result.json")["capture"], result)

    def test_missing_job_or_display_receipt_is_hold(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            allocation = root / "allocation"
            config, host, source = self.source_and_host(root)
            with patch.object(cli, "host_inputs", return_value=host), \
                 patch.object(cli, "windows_path", return_value=r"C:\dummy"), \
                 patch.object(cli.audit, "registration_values", return_value={"source": source}):
                plan = cli.prepare(allocation, 2, config)
            self.assertEqual(cli.adjudicate(allocation, plan["launch_plan_sha256"])["disposition"], "HOLD")

    def test_actual_arm_session_hook_uses_its_own_initial_and_terminal_witnesses(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            raw = root / "raw"
            runtime = raw / "arms/plain/runtime"
            runtime.mkdir(parents=True)
            private = root / "session"
            private.mkdir()
            context = {"raw": str(raw), "group": "/comparison.slice/unit.service",
                       "unit": "unit.service", "token": "0" * 32, "outer_display": ":120"}
            d = SimpleNamespace(query_keymap=lambda: [0] * 32, has_extension=lambda extension: extension == "XTEST",
                screen=lambda: SimpleNamespace(root=SimpleNamespace(
                    query_pointer=lambda: SimpleNamespace(mask=0))))

            class DummySession:
                def __init__(self):
                    self.xvfb = SimpleNamespace(pid=2051, poll=lambda: 0 if self.closed else None)
                    self.openbox = SimpleNamespace(pid=2052, poll=lambda: 0 if self.closed else None)
                    self.auth = private / "Xauthority"
                    self.auth.touch(mode=0o600)
                    self.display_num, self.name, self.env = 121, ":121", {}
                    self.tmp, self.d, self.closed = private, d, False

                def close(self):
                    self.closed = True

            original_read = Path.read_text
            original_exists = Path.exists

            def read(path, *args, **kwargs):
                if str(path) == "/tmp/.X121-lock":
                    return "2051\n"
                if path.name == "cgroup":
                    return "0::" + context["group"]
                return original_read(path, *args, **kwargs)

            def exists(path):
                return False if str(path) == "/tmp/.X121-lock" else original_exists(path)

            with patch.object(Path, "read_text", read), patch.object(Path, "exists", exists):
                session = x11.guarded_session(DummySession, context, runtime)()
                start = cli.audit.read(runtime / "comparison-display-start.json")
                self.assertEqual((start["arm"], start["scope"], start["pids"]),
                                 ("plain", "actual_comparison_arm_display", [2051, 2052]))
                self.assertFalse((runtime / "comparison-display-end.json").exists())
                session.close()
                end = cli.audit.read(runtime / "comparison-display-end.json")
                self.assertTrue(end["retired"])
                self.assertTrue(end["input_neutral_at_end"])
                self.assertTrue(session.closed)
                with self.assertRaisesRegex(ValueError, "outside the claimed"):
                    x11.guarded_session(DummySession, context, raw / "other/runtime")

    def completed_service_records(self, allocation, result):
        capture = SyntheticCapture(allocation)
        capture.populate()
        self.assertTrue(cli.failure_evidence.native_writers_retired(capture.out, require_all=True))
        plan = allocation / "launch-plan.json"
        cli.audit.write_record(plan, {
            "schema": "native_comparison_launch_plan_v1", "allocation": str(allocation),
            "service": cli.SERVICE_POLICY, "registration_sha256": capture.registration_digest,
        })
        plan_sha = cli.audit.digest(plan)
        token = "c" * 32
        unit = f"agent-interface-native-comparison-{token}.service"
        service = {**service_proof(unit), "unit": unit, "claim_token": token, "launch_plan_sha256": plan_sha}
        cli.audit.write_record(allocation / "claim.json", {
            "token": token, "unit": unit, "launch_plan_sha256": plan_sha, "automatic_retry": False,
        })
        cli.audit.write_record(allocation / "service-start.json", service)
        cli.audit.write_record(allocation / "service-result.json",
                               {"unit": unit, "claim_token": token, "returncode": 0})
        (capture.out / "capture.json").write_text(json.dumps(result), encoding="utf-8")
        cli.audit.write_record(allocation / "capture-worker-result.json", {
            "unit": unit, "claim_token": token, "capture": result,
        })
        display = display_proof(service)
        cli.audit.write_record(allocation / "display-start.json", display)
        cli.audit.write_record(allocation / "display-end.json", retire(display))
        (allocation / "service.stdout").touch()
        (allocation / "service.stderr").touch()
        for index, arm in enumerate(cli.audit.ARMS, start=1):
            runtime = capture.out / "arms" / arm / "runtime"
            timing = cli.audit.read(capture.out / "capture-arms" / arm / "arm-timing.json")
            proof = display_proof(service, number=121, pid=300 + index * 10, arm=arm,
                                  started=timing["arm_started_ns"] + 10)
            cli.audit.write_record(runtime / "comparison-display-start.json", proof)
            cli.audit.write_record(runtime / "comparison-display-end.json",
                {**retire(proof), "finished_monotonic_ns": timing["arm_finished_ns"] - 1})
        return capture, service, plan_sha

    def test_settled_persistent_failure_requires_independent_rejection_evidence(self):
        for wrong, settled in ((True, True), (False, True), (True, False)):
            with self.subTest(wrong=wrong, settled=settled), TemporaryDirectory() as directory:
                allocation = Path(directory)
                capture, service, plan_sha = self.completed_service_records(allocation, persistent_incomplete_capture())
                if wrong:
                    history = capture.out / "arms/persistent/runtime/submission-history.jsonl"
                    events = cli.audit.records(history)
                    events[3].update(submitted_values=["wrong"], exact=False)
                    history.write_text("".join(json.dumps(event) + "\n" for event in events), encoding="utf-8")
                if not settled:
                    (capture.out / "native-app-server" / "persistent" / cli.audit.APP_SERVER_JOB_RECEIPT).unlink()
                with (
                    patch.object(cli, "ROOT", capture.repo),
                    patch.object(cli, "failed_service_retired", return_value=True),
                    patch.object(cli, "cgroup_retired", return_value=True),
                ):
                    if not settled:
                        with self.assertRaisesRegex(ValueError, "all allocated native Windows writers"):
                            cli.seal_settled_capture(allocation, plan_sha, service["unit"], service["claim_token"])
                        self.assertFalse((capture.out / "capture-seal.json").exists())
                        continue
                    raw_sha, host_sha = cli.seal_settled_capture(
                        allocation, plan_sha, service["unit"], service["claim_token"])
                    outcome = cli.adjudicate(allocation, plan_sha, expected_seal=raw_sha, expected_host_seal=host_sha)
                self.assertEqual(outcome["disposition"], "REJECT" if wrong else "HOLD", outcome)
                if wrong:
                    self.assertEqual(outcome["reason"], "confirmed_persistent_safety_or_effect_failure")

    def test_actual_comparison_auditor_cannot_skip_invalid_host_or_missing_arm_proof(self):
        with TemporaryDirectory() as directory:
            allocation = Path(directory)
            capture, service, plan_sha = self.completed_service_records(allocation, complete_capture())
            seal = cli.audit.seal_capture(capture.out)
            cli.audit.write_record(allocation / "audit-anchor.json", {"seal_sha256": seal})
            host_seal = cli.seal_host(allocation, plan_sha)

            def audit_case(raw_sha, host_sha):
                return cli.adjudicate(allocation, plan_sha, expected_seal=raw_sha, expected_host_seal=host_sha)

            def rewrite(path, value):
                path.write_text(json.dumps(value), encoding="utf-8")

            with patch.object(cli, "ROOT", capture.repo), patch.object(cli, "cgroup_retired", return_value=True):
                valid = audit_case(seal, host_seal)
                self.assertEqual(valid["disposition"], "RETAIN", valid.get("reason"))
                file = allocation / "service-start.json"
                rewrite(file, {**service, "KillMode": "process", "MainPID": "0"})
                h = audit_case(seal, host_seal)
                self.assertEqual(h["disposition"], "HOLD")
                self.assertIn("retained host seal", h["reason"])
                host_path = allocation / "host-seal.json"
                rewrite(host_path, cli.host_seal_values(allocation, plan_sha))
                fake = audit_case(seal, cli.audit.digest(host_path))
                self.assertEqual(fake["disposition"], "HOLD")
                self.assertIn("effective limits", fake["reason"])

                rewrite(file, service)
                (capture.out / "arms/persistent/runtime/comparison-display-end.json").unlink()
                (capture.out / "capture-seal.json").unlink()
                raw_without_display = cli.audit.seal_capture(capture.out)
                rewrite(allocation / "audit-anchor.json", {"seal_sha256": raw_without_display})
                rewrite(host_path, cli.host_seal_values(allocation, plan_sha))
                missing = audit_case(raw_without_display, cli.audit.digest(host_path))
                self.assertEqual(missing["disposition"], "HOLD")
                self.assertIn("comparison-display-end.json", missing["reason"])


if __name__ == "__main__":
    unittest.main()
