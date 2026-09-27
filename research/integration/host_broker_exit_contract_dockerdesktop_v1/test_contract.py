from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import tempfile
import time
import unittest


ROOT = (Path(os.environ["BROKER_REPO_ROOT"]) if "BROKER_REPO_ROOT" in os.environ
        else Path(__file__).resolve().parents[3])
BROKER = Path(os.environ.get("BROKER_SOURCE_PATH", ROOT / "runtime" / "host_model_ipc_broker_v1.py"))
EVIDENCE = Path(os.environ.get("EVIDENCE_DIR", "/evidence"))
FAKE_SOURCE_PATH = Path(__file__).with_name("fake_codex.py")
FAKE_SOURCE = FAKE_SOURCE_PATH.read_bytes()


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, indent=2) + "\n", encoding="utf-8")


class BrokerDockerDesktopContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not BROKER.is_file():
            raise RuntimeError(f"frozen broker source missing: {BROKER}")
        EVIDENCE.mkdir(parents=True, exist_ok=True)
        cls.root = Path(tempfile.mkdtemp(prefix="broker-contract-", dir="/tmp"))
        cls.fake = cls.root / "fake-codex"
        cls.fake.write_bytes(FAKE_SOURCE)
        cls.fake.chmod(0o755)
        cls.records: list[dict] = []

    def run_case(self, name: str, *, requests: list[tuple[str, bytes]],
                 fake_exit: int = 0, fake_sleep_s: float = 0.0,
                 timeout_s: float = 2.0, executable: str | None = None,
                 idle_seconds: float | None = None) -> tuple[dict, Path]:
        case_dir = EVIDENCE / "cases" / name
        case_dir.mkdir(parents=True, exist_ok=True)
        ipc = Path(tempfile.mkdtemp(prefix=f"ipc-{name}-", dir="/tmp"))
        for filename, payload in requests:
            (ipc / filename).write_bytes(payload)
        env = os.environ.copy()
        env.update({"CODEX_EXE": executable or str(self.fake),
                    "HOST_MODEL_BROKER_TIMEOUT_S": str(timeout_s),
                    "FAKE_EXIT": str(fake_exit), "FAKE_SLEEP_S": str(fake_sleep_s),
                    "FAKE_STDOUT": '{"fake":true}\n', "FAKE_STDERR": "fake-stderr\n",
                    "FAKE_CAPTURE_PATH": str(case_dir / "child.json")})
        command = [sys.executable, str(BROKER), "--ipc", str(ipc), "--repo", str(ROOT), "--once"]
        started = time.monotonic_ns()
        if idle_seconds is None:
            proc = subprocess.run(command, env=env, text=True, capture_output=True, timeout=8)
            process_record = {"returncode": proc.returncode, "stdout": proc.stdout,
                              "stderr": proc.stderr, "duration_ns": time.monotonic_ns() - started}
        else:
            proc = subprocess.Popen(command, env=env, text=True, stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE)
            time.sleep(idle_seconds)
            alive_at_deadline = proc.poll() is None
            proc.terminate()
            out, err = proc.communicate(timeout=3)
            process_record = {"returncode": proc.returncode, "stdout": out, "stderr": err,
                              "alive_at_deadline": alive_at_deadline,
                              "observed_idle_ns": time.monotonic_ns() - started}
        files = {p.name: p.read_bytes() for p in sorted(ipc.iterdir()) if p.is_file()}
        broker_bytes = files.get(next((n for n in files if n.endswith(".broker.json")), ""))
        response_bytes = files.get(next((n for n in files if n.endswith(".response.jsonl")), ""))
        receipt_value = json.loads(broker_bytes) if broker_bytes else None
        child_path = case_dir / "child.json"
        child = json.loads(child_path.read_text(encoding="utf-8")) if child_path.exists() else None
        record = {"case": name,
                  "requests": [{"filename": fn, "bytes_hex": payload.hex(), "sha256": sha256(payload)}
                               for fn, payload in requests],
                  "command": command, "fake_source_sha256": sha256(FAKE_SOURCE),
                  "execution_config": {"executable": executable or str(self.fake),
                                       "executable_sha256": sha256(FAKE_SOURCE) if executable is None else None,
                                       "fake_exit": fake_exit, "fake_sleep_s": fake_sleep_s,
                                       "broker_timeout_s": timeout_s,
                                       "idle_observation_s": idle_seconds},
                  "process": process_record,
                  "broker_receipt": receipt_value,
                  "broker_receipt_bytes_hex": broker_bytes.hex() if broker_bytes else None,
                  "response_bytes_hex": response_bytes.hex() if response_bytes is not None else None,
                  "response_sha256": sha256(response_bytes) if response_bytes is not None else None,
                  "child_stdout_bytes_hex": response_bytes.hex() if response_bytes is not None else None,
                  "broker_stderr_text": receipt_value.get("stderr") if receipt_value else None,
                  "child": child,
                  "ipc_files": sorted(files),
                  "observed": {"receipt_count": sum(n.endswith(".broker.json") for n in files),
                               "response_count": sum(n.endswith(".response.jsonl") for n in files)}}
        write_json(case_dir / "raw.json", record)
        self.records.append(record)
        return record, case_dir

    @staticmethod
    def request(request_id: str) -> bytes:
        return (json.dumps({"request_id": request_id, "prompt": "deterministic fake-only probe",
                            "schema": "/repo/runtime/fake-schema.json",
                            "working": "/repo"}, sort_keys=True) + "\n").encode()

    def test_01_exit_zero_receipt_vs_broker_status(self):
        record, _ = self.run_case("exit-zero", requests=[("01.request.json", self.request("req-zero"))])
        self.assertEqual(record["broker_receipt"]["returncode"], 0)
        self.assertEqual(record["child"]["configured_exit"], 0)
        self.assertEqual(record["process"]["returncode"], 1)

    def test_02_nonzero_exit_is_propagated(self):
        record, _ = self.run_case("exit-23", requests=[("01.request.json", self.request("req-23"))],
                                  fake_exit=23)
        self.assertEqual(record["broker_receipt"]["returncode"], 23)
        self.assertEqual(record["process"]["returncode"], 23)

    def test_03_timeout_is_typed_and_nonzero(self):
        record, _ = self.run_case("timeout", requests=[("01.request.json", self.request("req-timeout"))],
                                  fake_sleep_s=1.0, timeout_s=0.1)
        self.assertIsNone(record["broker_receipt"]["returncode"])
        self.assertEqual(record["broker_receipt"]["error_class"], "TimeoutExpired")
        self.assertEqual(record["broker_receipt"]["stop_reason"], "HOST_BROKER_SUBPROCESS_TIMEOUT")
        self.assertNotEqual(record["process"]["returncode"], 0)

    def test_04_unavailable_executable_is_typed_and_nonzero(self):
        record, _ = self.run_case("unavailable", requests=[("01.request.json", self.request("req-missing"))],
                                  executable="/tmp/no-such-fake-codex")
        self.assertIsNone(record["broker_receipt"]["returncode"])
        self.assertEqual(record["broker_receipt"]["error_class"], "FileNotFoundError")
        self.assertEqual(record["broker_receipt"]["stop_reason"], "HOST_BROKER_EXECUTABLE_UNAVAILABLE")
        self.assertNotEqual(record["process"]["returncode"], 0)

    def test_05_malformed_request_fails_without_receipt(self):
        record, _ = self.run_case("malformed", requests=[("01.request.json", b"{not-json\n")])
        self.assertNotEqual(record["process"]["returncode"], 0)
        self.assertIsNone(record["broker_receipt"])
        self.assertEqual(record["observed"]["receipt_count"], 0)
        self.assertEqual(record["observed"]["response_count"], 0)
        self.assertIn("JSONDecodeError", record["process"]["stderr"])

    def test_06_no_request_remains_idle_within_bounded_observation(self):
        record, _ = self.run_case("no-request", requests=[], idle_seconds=0.2)
        self.assertTrue(record["process"]["alive_at_deadline"])
        self.assertEqual(record["observed"]["receipt_count"], 0)
        self.assertEqual(record["observed"]["response_count"], 0)
        self.assertEqual(record["ipc_files"], [])

    def test_07_once_processes_only_first_sorted_request(self):
        record, _ = self.run_case("one-shot-two-requests", requests=[
            ("01.request.json", self.request("req-A")),
            ("02.request.json", self.request("req-B"))])
        self.assertEqual(record["broker_receipt"]["request_id"], "req-A")
        self.assertEqual(record["observed"]["receipt_count"], 1)
        self.assertEqual(record["observed"]["response_count"], 1)
        self.assertIn("02.request.json", record["ipc_files"])
        self.assertEqual(record["process"]["returncode"], 1)


def main() -> int:
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(BrokerDockerDesktopContract)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    records = BrokerDockerDesktopContract.records
    inventory = {}
    for path in sorted(EVIDENCE.rglob("*")):
        if path.is_file() and path.name not in {"raw_inventory.json", "formal_summary.json"}:
            inventory[path.relative_to(EVIDENCE).as_posix()] = sha256(path.read_bytes())
    write_json(EVIDENCE / "formal_summary.json", {
        "tests_run": result.testsRun, "failures": len(result.failures), "errors": len(result.errors),
        "formal_status": "CHARACTERIZATION_COMPLETE" if result.wasSuccessful() else "CHARACTERIZATION_TEST_FAILURE",
        "hypothesis_disposition": "FAIL_ZERO_EXIT_PROPAGATION" if any(
            r["case"] == "exit-zero" and r["broker_receipt"] and r["broker_receipt"].get("returncode") == 0
            and r["process"].get("returncode") != 0 for r in records) else "NO_PREDICTED_MISMATCH",
        "container": {"python": sys.version, "platform": platform.platform(), "machine": platform.machine()},
        "case_order": [r["case"] for r in records],
        "fake_source_sha256": sha256(FAKE_SOURCE),
        "broker_source_sha256": sha256(BROKER.read_bytes()),
    })
    for path in sorted(EVIDENCE.rglob("*")):
        if path.is_file() and path.name not in {"raw_inventory.json", "formal_summary.json"}:
            inventory[path.relative_to(EVIDENCE).as_posix()] = sha256(path.read_bytes())
    write_json(EVIDENCE / "raw_inventory.json", inventory)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
