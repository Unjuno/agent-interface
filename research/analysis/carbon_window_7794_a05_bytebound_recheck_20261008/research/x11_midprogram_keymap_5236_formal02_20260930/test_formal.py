import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]
PACKAGE = "research.x11_midprogram_keymap_5236_formal02_20260930"
EXPECTED_HEX = "7b227361766564223a20747275652c202274657874223a2022615f227d0a"


def completed_row(row_id, initial, target):
    wait = {"started_ns": 1_000_000_000, "ended_ns": 2_500_000_000}
    actor = None if target is None else {
        "target_layout": target,
        "started_ns": 1_250_000_000,
        "ended_ns": 1_260_000_000,
        "exit": 0,
        "argv": ["setxkbmap", "-display", ":91", "-layout", target],
    }
    return {
        "row": row_id,
        "display": ":91",
        "initial_layout": initial,
        "target_layout": target,
        "layout_setup": {"argv": ["setxkbmap", "-display", ":91", "-layout", initial], "exit": 0, "stdout": "", "stderr": ""},
        "layout_initial": {"argv": ["setxkbmap", "-display", ":91", "-query"], "exit": 0, "stdout": f"layout: {initial}\n", "stderr": ""},
        "layout_after": {"argv": ["setxkbmap", "-display", ":91", "-query"], "exit": 0, "stdout": f"layout: {target or initial}\n", "stderr": ""},
        "actor_argv": None if target is None else ["/usr/sbin/python", "-c", "actor", ":91", target, "actor.json"],
        "actor_receipt": actor,
        "wait": wait,
        "program": {
            "schema": "agent-interface/program-v1",
            "program_id": "issue5236-formal02-" + row_id,
            "source": {"observation_seq": 7, "binding_revision": 3},
            "terminal": {"release_all_required": True},
            "ops": [
                {"op": "focus", "target": "fixture"},
                {"op": "text", "text": "a"},
                {"op": "wait_update", "timeout_ms": 1500},
                {"op": "text", "text": "_"},
                {"op": "key_chord", "keys": ["CTRL", "S"]},
                {"op": "release_all"},
            ],
        },
        "dispatch": {
            "status": "completed",
            "execution": {
                "completed_ops": [0, 1, 2, 3, 4, 5],
                "waits": [wait],
                "releases": [{"verified": True, "keys_down": [], "buttons_down": []}],
            },
        },
        "saved_effect_hex": EXPECTED_HEX,
        "expected_effect_hex": EXPECTED_HEX,
        "fixture_exit": -15,
        "xvfb": {
            "argv": ["Xvfb", "-displayfd", "1", "-screen", "0", "1024x768x24", "-nolisten", "tcp", "-terminate", "-ac"],
            "exit_code": 0,
            "cleanup_action": "natural_terminate",
        },
    }


def sample_raw():
    return {
        "schema": "issue5236-formal02-raw-v1",
        "source_manifest": {"files": {"runtime/backends/x11_v1/backend.py": "backend-blob"}},
        "source_blobs": {"runtime/backends/x11_v1/backend.py": "backend-blob"},
        "namespace": {
            "host_mount_ns_inode": 4026532221,
            "child_mount_ns_inode": 4026532299,
            "private": True,
            "socket_mount": {"target": "/tmp/.X11-unix", "fstype": "tmpfs", "source": "none"},
            "socket_dir_mode": 0o1777,
        },
        "rows": [
            completed_row("control_us", "us", None),
            completed_row("jp_to_us", "jp", "us"),
            completed_row("us_to_jp", "us", "jp"),
        ],
    }


def sample_wrapper():
    identity = {"mode": 0o777, "inode": 2, "device": 38}
    return {
        "schema": "issue5236-formal02-wrapper-v1",
        "command": ["unshare", "--user", "--map-root-user", "--mount", "--fork", "python", "runner.py", "--child"],
        "source_manifest": {"files": {"runtime/backends/x11_v1/backend.py": "backend-blob"}},
        "timeout": False,
        "returncode": 0,
        "host_mount_ns_inode": 4026532221,
        "host_socket_before": identity,
        "host_socket_after": identity,
        "host_socket_unchanged": True,
        "child_raw_available": True,
    }


class FormalAuditTests(unittest.TestCase):
    def invoke_audit(self, raw, wrapper=None):
        with tempfile.TemporaryDirectory() as temp:
            raw_path = Path(temp) / "raw.json"
            wrapper_path = Path(temp) / "wrapper.json"
            raw_path.write_text(json.dumps(raw), encoding="utf-8")
            wrapper_path.write_text(json.dumps(wrapper or sample_wrapper()), encoding="utf-8")
            return subprocess.run(
                [sys.executable, "-B", "-m", f"{PACKAGE}.audit", str(raw_path), str(wrapper_path)],
                cwd=ROOT, capture_output=True, text=True, timeout=10,
            )

    def test_exact_three_rows_classify_as_no_stale_effect(self):
        result = self.invoke_audit(sample_raw())
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["decision"], "NO_STALE_EFFECT_OBSERVED", result.stdout)

    def test_wrong_completed_remap_effect_is_scientific_fail_not_pass(self):
        raw = sample_raw()
        raw["rows"][1]["saved_effect_hex"] = "7b227361766564223a20747275652c202274657874223a20226129227d0a"
        result = self.invoke_audit(raw)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["decision"], "FAIL_STALE_MAP_EFFECT")

    def test_two_remap_rows_fail_closed_only_with_verified_release(self):
        raw = sample_raw()
        for row in raw["rows"][1:]:
            row["dispatch"] = {
                "status": "execution_failed",
                "execution": {
                    "failed_op": 3,
                    "completed_ops": [0, 1, 2],
                    "waits": [row["wait"]],
                    "releases": [{"verified": True, "keys_down": [], "buttons_down": []}],
                },
            }
            row["saved_effect_hex"] = None
        result = self.invoke_audit(raw)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["decision"], "PASS_MIDPROGRAM_REMAP_FAIL_CLOSED", result.stdout)

        raw["rows"][2]["dispatch"]["execution"]["releases"][0]["verified"] = False
        unsafe = self.invoke_audit(raw)
        self.assertEqual(unsafe.returncode, 0, unsafe.stderr)
        self.assertEqual(json.loads(unsafe.stdout)["decision"], "STOP_PROVENANCE_OR_RUNNER")

    def test_actor_outside_wait_is_provenance_stop(self):
        raw = sample_raw()
        raw["rows"][1]["actor_receipt"]["started_ns"] = 999_000_000
        result = self.invoke_audit(raw)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["decision"], "STOP_PROVENANCE_OR_RUNNER")

    def test_namespace_binding_mount_and_host_socket_are_audited(self):
        raw = sample_raw()
        raw["namespace"]["host_mount_ns_inode"] += 1
        result = self.invoke_audit(raw)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["decision"], "STOP_PROVENANCE_OR_RUNNER")

    def test_source_manifest_mismatch_is_provenance_stop(self):
        raw = sample_raw()
        raw["source_blobs"]["runtime/backends/x11_v1/backend.py"] = "changed-blob"
        result = self.invoke_audit(raw)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["decision"], "STOP_PROVENANCE_OR_RUNNER")

    def test_wrapper_must_create_user_and_mount_namespaces(self):
        wrapper = sample_wrapper()
        wrapper["command"] = ["python", "runner.py", "--child"]
        result = self.invoke_audit(sample_raw(), wrapper)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["decision"], "STOP_PROVENANCE_OR_RUNNER")

    def test_five_corruption_controls_reject_mutated_raw(self):
        with tempfile.TemporaryDirectory() as temp:
            raw_path = Path(temp) / "raw.json"
            wrapper_path = Path(temp) / "wrapper.json"
            raw_path.write_text(json.dumps(sample_raw()), encoding="utf-8")
            wrapper_path.write_text(json.dumps(sample_wrapper()), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, "-B", "-m", f"{PACKAGE}.corruptions", str(raw_path), str(wrapper_path)],
                cwd=ROOT, capture_output=True, text=True, timeout=10,
            )
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertTrue(report["all_rejected"])
        self.assertEqual(
            [row["name"] for row in report["controls"]],
            ["omitted_row", "swapped_direction", "wrong_expected_bytes", "missing_actor_receipt", "changed_raw_output"],
        )
        self.assertEqual(report["controls"][-1]["decision"], "FAIL_STALE_MAP_EFFECT")


class FormalRunnerGuardTests(unittest.TestCase):
    def invoke_runner(self, output):
        return subprocess.run(
            [sys.executable, "-B", "-m", f"{PACKAGE}.runner", "--output", str(output)],
            cwd=ROOT, capture_output=True, text=True, timeout=10,
        )

    def test_existing_output_path_is_refused_without_modification(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as temp:
            output = Path(temp) / "exists"
            output.mkdir()
            marker = output / "owner.txt"
            marker.write_text("keep", encoding="utf-8")
            result = self.invoke_runner(output)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("STOP_OUTPUT_COLLISION", result.stderr)
            self.assertEqual(marker.read_text(encoding="utf-8"), "keep")

    def test_output_path_outside_checkout_is_refused_before_creation(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "not-in-checkout"
            result = self.invoke_runner(output)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("STOP_OUTPUT_PATH_OUTSIDE_REPO", result.stderr)
            self.assertFalse(output.exists())

    def test_output_path_must_match_the_frozen_unique_allocation(self):
        output = ROOT / "research" / "x11_midprogram_keymap_5236_formal02_20260930" / "results" / "not-frozen"
        self.assertFalse(output.exists())
        result = self.invoke_runner(output)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("STOP_OUTPUT_PATH_UNFROZEN", result.stderr)
        self.assertFalse(output.exists())

    def test_bounded_child_timeout_retains_output_and_reaps_process(self):
        from .runner import run_bounded

        result = run_bounded(
            [sys.executable, "-c", "import time; print('CHILD-READY',flush=True); time.sleep(5)"],
            timeout=0.15,
        )
        self.assertTrue(result["timeout"])
        self.assertIn("CHILD-READY", result["stdout"])
        self.assertNotEqual(result["returncode"], 0)

    def test_source_manifest_rejects_blob_change(self):
        from .runner import source_manifest_errors

        from .runner import source_blob_id

        relative = "runtime/backends/x11_v1/backend.py"
        blob = source_blob_id(ROOT / relative)
        manifest = {"files": {relative: blob}}
        self.assertEqual(source_manifest_errors(manifest, ROOT), [])
        manifest["files"][relative] = "0" * 40
        self.assertIn(relative, " ".join(source_manifest_errors(manifest, ROOT)))

    def test_checked_in_manifest_has_no_self_reference_and_matches_sources(self):
        import json
        from .runner import source_manifest_errors

        path = Path(__file__).with_name("SOURCE_MANIFEST.json")
        manifest = json.loads(path.read_text(encoding="utf-8"))
        self.assertNotIn(path.relative_to(ROOT).as_posix(), manifest["files"])
        self.assertEqual(source_manifest_errors(manifest, ROOT), [])

    def test_server_is_reaped_when_xlib_anchor_setup_raises(self):
        from . import runner

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            binary = root / "bin"
            binary.mkdir()
            pid_file = root / "fake-xvfb.pid"
            fake = binary / "Xvfb"
            fake.write_text(
                "#!/bin/sh\nprintf '%s\\n' \"$$\" > \"$FAKE_XVFB_PID_FILE\"\nprintf '91\\n'\nexec sleep 60\n",
                encoding="utf-8",
            )
            fake.chmod(0o755)
            row_dir = root / "row"
            row_dir.mkdir()
            original_popen = subprocess.Popen
            spawned = []

            def tracking_popen(*args, **kwargs):
                process = original_popen(*args, **kwargs)
                spawned.append(process)
                return process

            with patch.dict(os.environ, {"PATH": f"{binary}:/usr/bin:/bin:/usr/sbin", "FAKE_XVFB_PID_FILE": str(pid_file)}), \
                    patch.object(runner.subprocess, "Popen", tracking_popen), \
                    patch.object(runner, "XDisplay", side_effect=RuntimeError("injected anchor failure")):
                with self.assertRaisesRegex(RuntimeError, "injected anchor failure"):
                    runner._start_server(row_dir)
            try:
                self.assertEqual(len(spawned), 1)
                self.assertIsNotNone(spawned[0].poll(), "failed anchor setup left Xvfb alive")
            finally:
                if spawned and spawned[0].poll() is None:
                    spawned[0].send_signal(signal.SIGTERM)
                    spawned[0].wait(timeout=3)


if __name__ == "__main__":
    unittest.main(verbosity=2)
