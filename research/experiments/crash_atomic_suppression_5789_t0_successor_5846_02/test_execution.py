"""Host-only construction rehearsal; never a formal/container allocation."""

import json
import hashlib
import gc
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import warnings
from unittest import mock

import protocol
import runner
import container_runner


class ProcessMatrixConstructionTests(unittest.TestCase):
    def test_container_candidate_command_is_isolated_bounded_and_pinned(self):
        command = container_runner.docker_command(
            docker="docker",
            context="assigned-guest",
            platform="linux/arm64",
            source=Path("/source"),
            output=Path("/candidate-out"),
            runtime={"source_commit": "a" * 40, "image_id": "sha256:" + "b" * 64,
                     "docker_host": "tcp://isolated-guest:2376"},
            freeze_digest="c" * 64,
            mode="formal",
            include_manifest=True,
        )
        for required in (
            "--network", "none", "--read-only", "--cpus", "1", "--memory", "256m",
            "--pids-limit", "64", "linux/arm64", "--mount",
        ):
            self.assertIn(required, command)
        self.assertIn(container_runner.IMAGE, command)
        self.assertIn("readonly", " ".join(command))
        self.assertIn("--network", command)
        self.assertEqual(command.count("--network"), 1)
        self.assertIn("OBSTAC_DOCKER_HOST", " ".join(command))
        self.assertIn("OBSTAC_AUDIT_SHA256", " ".join(command))

    def test_formal_launcher_freeze_covers_launcher_bytes_and_exact_argv(self):
        import argparse
        args = argparse.Namespace(
            mode="formal", candidate_out=Path("results/formal-01/candidate"),
            audit_out=Path("results/formal-01/audit"),
            audit_raw=Path("results/formal-01/candidate/raw.jsonl"), docker="docker",
        )
        argv = container_runner.invocation_argv(args)
        self.assertEqual(argv[argv.index("--mode") + 1], "formal")
        self.assertEqual(argv[argv.index("--docker") + 1], "docker")
        self.assertEqual(argv[argv.index("--audit-out") + 1],
                         "results/formal-01/audit")
        self.assertEqual(argv[2], "/study/container_runner.py")
        self.assertEqual(container_runner.sha256(Path(container_runner.__file__)),
                         hashlib.sha256(Path(container_runner.__file__).read_bytes()).hexdigest())

    def test_guest_path_uses_frozen_host_mount_root_not_guest_file_parent(self):
        host_root = Path("/private/work/repo/research/experiments/package")
        mapped = container_runner.guest_path(
            Path("/study/results/formal-02/candidate"), host_root
        )
        self.assertEqual(
            mapped,
            host_root / "results/formal-02/candidate",
        )

    def test_guest_path_rejects_paths_outside_assigned_mount(self):
        with self.assertRaisesRegex(SystemExit, "STOP_PATH_OUTSIDE_ASSIGNED_GUEST_MOUNT"):
            container_runner.guest_path(Path("/tmp/not-mounted"), Path("/host/package"))
        with self.assertRaisesRegex(SystemExit, "STOP_HOST_SOURCE_ROOT_NOT_ABSOLUTE"):
            container_runner.guest_path(Path("/study/raw.jsonl"), Path("relative/package"))

    def test_formal_host_argv_is_absolute_after_guest_path_translation(self):
        import argparse
        host_root = Path("/private/work/repo/research/experiments/package")
        args = argparse.Namespace(
            mode="formal", candidate_out=Path("/study/results/5846-02/candidate"),
            audit_out=Path("/study/results/5846-02/audit"),
            audit_raw=Path("/study/results/5846-02/candidate/raw.jsonl"), docker="docker",
        )
        host_args = argparse.Namespace(
            mode=args.mode,
            candidate_out=container_runner.guest_path(args.candidate_out, host_root),
            audit_out=container_runner.guest_path(args.audit_out, host_root),
            audit_raw=container_runner.guest_path(args.audit_raw, host_root),
            docker=args.docker,
        )
        argv = container_runner.invocation_argv(host_args)
        self.assertEqual(argv[argv.index("--candidate-out") + 1],
                         str(host_root / "results/5846-02/candidate"))
        self.assertEqual(argv[argv.index("--audit-out") + 1],
                         str(host_root / "results/5846-02/audit"))
        self.assertEqual(argv[argv.index("--audit-raw") + 1],
                         str(host_root / "results/5846-02/candidate/raw.jsonl"))

    def test_auditor_mounts_a_report_directory_not_a_file_as_directory(self):
        with tempfile.TemporaryDirectory(prefix="construction-5795-audit-command-") as temp:
            root = Path(temp)
            candidate = root / "candidate"
            audit = root / "audit"
            candidate.mkdir()
            audit.mkdir()
            with mock.patch.object(container_runner, "load_freeze") as mocked_freeze, \
                 mock.patch.object(container_runner, "verify_context_endpoint"), \
                 mock.patch.object(container_runner.subprocess, "run", return_value=mock.Mock(returncode=0)) as mocked_run:
                manifest = {
                    "audit_sha256": container_runner.sha256(container_runner.BASE / "audit.py"),
                    "runtime": {
                        "docker_context": "assigned-context",
                        "docker_host": "unix:///var/run/docker.sock",
                        "platform": "linux/arm64",
                        "source_commit": "a" * 40,
                        "image_id": "sha256:" + "b" * 64,
                        "host_source_root": str(Path("/host/package")),
                    },
                }
                digest = "c" * 64
                manifest["launcher_sha256"] = container_runner.sha256(Path(container_runner.__file__))
                manifest["formal_argv"] = [
                    "python3", "-B", "/study/container_runner.py",
                    "--mode", "formal", "--candidate-out", str(candidate.resolve()),
                    "--audit-out", str(audit.resolve()), "--audit-raw",
                    str((candidate / "raw.jsonl").resolve()), "--docker", "docker",
                ]
                mocked_freeze.return_value = (manifest, digest)
                env = {
                    "OBSTAC_RUN_KIND": "formal",
                    "OBSTAC_DOCKER_CONTEXT": "assigned-context",
                    "OBSTAC_DOCKER_HOST": "unix:///var/run/docker.sock",
                    "OBSTAC_AUDIT_SHA256": manifest["audit_sha256"],
                    "OBSTAC_FREEZE_SHA256": digest,
                    "OBSTAC_SOURCE_COMMIT": "a" * 40,
                    "OBSTAC_IMAGE_ID": "sha256:" + "b" * 64,
                    "OBSTAC_PLATFORM": "linux/arm64",
                }
                def create_raw(*args, **kwargs):
                    (candidate / "raw.jsonl").write_text("{}\n")
                    return 0
                with mock.patch.object(container_runner, "guest_path", side_effect=lambda path, _root: path.resolve()), \
                     mock.patch.object(container_runner, "run_candidate", side_effect=create_raw), \
                     mock.patch.dict(os.environ, env, clear=False), \
                     mock.patch.object(sys, "argv", [
                         "container_runner.py", "--mode", "formal",
                         "--candidate-out", str(candidate), "--audit-out", str(audit),
                         "--audit-raw", str(candidate / "raw.jsonl"),
                     ]):
                    self.assertEqual(container_runner.main(), 0)
            audit_command = mocked_run.call_args.args[0]
            out_index = audit_command.index("--out")
            self.assertEqual(audit_command[out_index + 1], "/work/out")
            self.assertIn(f"src={audit.resolve()},dst=/work/out", " ".join(audit_command))

    def test_formal_container_runner_refuses_missing_allocation_before_docker(self):
        with tempfile.TemporaryDirectory(prefix="construction-5795-launcher-") as temp:
            root = Path(temp)
            out = root / "candidate"
            env = {key: value for key, value in os.environ.items()
                   if not key.startswith("OBSTAC_")}
            proc = subprocess.run(
                [sys.executable, "-B", str(Path(container_runner.__file__)),
                 "--mode", "formal", "--candidate-out", str(out)],
                capture_output=True,
                text=True,
                timeout=10,
                env=env,
            )
            self.assertNotEqual(proc.returncode, 0)
            self.assertIn("STOP_NO_FORMAL_ALLOCATION", proc.stderr)
            self.assertFalse(out.exists())

    def test_construction_container_runner_uses_only_named_construction_endpoint(self):
        with tempfile.TemporaryDirectory(prefix="construction-5795-construction-launch-") as temp:
            root = Path(temp)
            out = root / "out"
            env = {key: value for key, value in os.environ.items()
                   if not key.startswith("OBSTAC_")}
            env.update({
                "OBSTAC_CONSTRUCTION_CONTEXT": "isolated-construction-context",
                "OBSTAC_CONSTRUCTION_DOCKER_HOST": "tcp://construction-guest:2376",
            })
            previous = {key: os.environ.get(key) for key in (
                "OBSTAC_CONSTRUCTION_CONTEXT", "OBSTAC_CONSTRUCTION_DOCKER_HOST"
            )}
            with mock.patch.object(container_runner.subprocess, "run") as mocked_run:
                mocked_run.side_effect = [
                    mock.Mock(returncode=0, stdout='"tcp://construction-guest:2376"', stderr=""),
                    mock.Mock(returncode=0),
                ]
                try:
                    os.environ.update(env)
                    with mock.patch.object(sys, "argv", [
                        str(Path(container_runner.__file__)), "--mode", "construction",
                        "--candidate-out", str(out),
                    ]):
                        self.assertEqual(container_runner.main(), 0)
                finally:
                    for key, value in previous.items():
                        if value is None:
                            os.environ.pop(key, None)
                        else:
                            os.environ[key] = value
            command = mocked_run.call_args.args[0]
            self.assertIn("--context", command)
            self.assertIn("isolated-construction-context", command)
            self.assertNotIn("--host", command)
            self.assertIn("--construction", command)
            self.assertIn("--network", command)
            self.assertFalse(any("orbstack" in item for item in command))

    def test_audit_requires_frozen_mode_and_hash(self):
        with tempfile.TemporaryDirectory(prefix="construction-5795-audit-gate-") as temp:
            root = Path(temp)
            raw = root / "raw.jsonl"
            raw.write_text("[]\n")
            out = root / "audit"
            proc = subprocess.run(
                [sys.executable, "-B", str(Path(__file__).with_name("audit.py")),
                 "--raw", str(raw), "--out", str(out)],
                capture_output=True,
                text=True,
                timeout=10,
            )
            self.assertNotEqual(proc.returncode, 0)
            self.assertIn("STOP_AUDIT_RUN_KIND", proc.stderr)
            self.assertFalse(out.exists())

    def test_formal_gate_rejects_missing_or_mismatched_freeze_before_rows(self):
        with tempfile.TemporaryDirectory(prefix="construction-5795-gate-") as temp:
            root = Path(temp)
            freeze_path = Path(runner.__file__).with_name("FREEZE.json")
            original = freeze_path.read_bytes() if freeze_path.exists() else None
            try:
                freeze_path.unlink(missing_ok=True)
                env = {key: value for key, value in os.environ.items()
                       if not key.startswith("OBSTAC_")}
                proc = subprocess.run(
                    [sys.executable, "-B", str(Path(runner.__file__)),
                     "--out", str(root / "out")],
                    capture_output=True,
                    text=True,
                    timeout=10,
                    env=env,
                )
            finally:
                if original is not None:
                    freeze_path.write_bytes(original)
            self.assertNotEqual(proc.returncode, 0)
            self.assertIn("STOP_FREEZE_MANIFEST", proc.stderr)
            self.assertTrue((root / "out").is_dir())
            self.assertEqual(list((root / "out").iterdir()), [])

    def test_formal_gate_rejects_source_drift_before_rows(self):
        with tempfile.TemporaryDirectory(prefix="construction-5795-gate-ok-") as temp:
            root = Path(temp)
            manifest = {
                "source_sha256": {"deliberately_stale": "0" * 64},
                "schedule_sha256": protocol.schedule_sha256(),
                "runtime": {
                    "run_kind": "formal",
                    "docker_context": "assigned-isolated-context",
                    "platform": "linux/arm64",
                    "source_commit": "a" * 40,
                    "image_id": "sha256:" + "b" * 64,
                },
            }
            env = os.environ.copy()
            env.update({
                "OBSTAC_RUN_KIND": "formal",
                "OBSTAC_DOCKER_CONTEXT": "assigned-isolated-context",
                "OBSTAC_PLATFORM": "linux/arm64",
                "OBSTAC_SOURCE_COMMIT": "a" * 40,
                "OBSTAC_IMAGE_ID": "sha256:" + "b" * 64,
                "OBSTAC_FREEZE_SHA256": hashlib.sha256(
                    json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode()
                ).hexdigest(),
            })
            freeze_path = Path(runner.__file__).with_name("FREEZE.json")
            original = freeze_path.read_bytes() if freeze_path.exists() else None
            try:
                freeze_path.write_text(json.dumps(manifest, sort_keys=True) + "\n")
                proc = subprocess.run(
                    [sys.executable, "-B", str(Path(__file__).with_name("runner.py")),
                     "--out", str(root / "out")],
                    capture_output=True,
                    text=True,
                    timeout=10,
                    env=env,
                )
            finally:
                if original is None:
                    freeze_path.unlink(missing_ok=True)
                else:
                    freeze_path.write_bytes(original)
            self.assertNotEqual(proc.returncode, 0)
            self.assertIn("STOP_SOURCE_HASH_MISMATCH", proc.stderr)
            self.assertEqual(list((root / "out").iterdir()), [])

    def test_sigkill_child_pipes_are_closed_without_resource_warning(self):
        with tempfile.TemporaryDirectory(prefix="construction-5795-pipes-") as temp:
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always", ResourceWarning)
                runner.run_row(protocol.CASES[4], Path(temp))
                gc.collect()
            resource_warnings = [w for w in caught if issubclass(w.category, ResourceWarning)]
            self.assertEqual(resource_warnings, [])

    def test_sigkill_case_is_reaped_before_next_acknowledged_child(self):
        with tempfile.TemporaryDirectory(prefix="construction-5795-reap-") as temp:
            root = Path(temp)
            cut = runner.run_row(protocol.CASES[4], root)
            self.assertEqual(cut["persist"]["returncode"], -9)
            ack = runner.run_row(protocol.CASES[6], root)
            self.assertEqual(ack["persist"]["returncode"], 0)
            self.assertEqual(ack["ack_state"], "ACKNOWLEDGED")

    def test_full_process_matrix_and_raw_only_audit_cli(self):
        with tempfile.TemporaryDirectory(prefix="construction-5795-") as temp:
            root = Path(temp)
            scratch = root / "scratch"
            scratch.mkdir()
            rows = [runner.run_row(spec, scratch) for spec in protocol.CASES]
            raw = root / "raw.jsonl"
            raw.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows))
            report = root / "audit-out"
            report.mkdir()
            import hashlib
            audit_env = os.environ.copy()
            audit_env.update({
                "OBSTAC_RUN_KIND": "formal",
                "OBSTAC_PLATFORM": "linux/arm64",
                "OBSTAC_AUDIT_SHA256": hashlib.sha256(
                    Path(__file__).with_name("audit.py").read_bytes()
                ).hexdigest(),
            })
            audited = subprocess.run(
                [sys.executable, "-B", str(Path(__file__).with_name("audit.py")),
                 "--raw", str(raw), "--out", str(report)],
                capture_output=True,
                text=True,
                timeout=15,
                env=audit_env,
            )
            self.assertEqual(audited.returncode, 0, audited.stderr + audited.stdout)
            result = json.loads((report / "audit.json").read_text())
            self.assertEqual(result["decision"], "PASS_CRASH_ATOMIC_SUPPRESSION_T0_SCOPED")
            self.assertEqual(result["rows"], 15)
            self.assertEqual(result["candidate_rows_matching_frozen_gate"], 10)
            self.assertTrue(result["baseline_failures_reproduced"])

            lines = raw.read_text().splitlines()
            mutated = json.loads(lines[12])
            mutated["gc"]["retained"] = False
            tampered = root / "tampered.jsonl"
            lines[12] = json.dumps(mutated, sort_keys=True)
            tampered.write_text("\n".join(lines) + "\n")
            tamper_out = root / "tamper-audit"
            tamper_out.mkdir()
            rejected = subprocess.run(
                [sys.executable, "-B", str(Path(__file__).with_name("audit.py")),
                 "--raw", str(tampered), "--out", str(tamper_out)],
                capture_output=True,
                text=True,
                timeout=15,
                env=audit_env,
            )
            self.assertEqual(rejected.returncode, 2)
            self.assertIn("gc_tombstone_retention", json.loads(
                (tamper_out / "audit.json").read_text()
            )["errors"][-1])


if __name__ == "__main__":
    unittest.main()
