import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


WRAPPER = Path(__file__).with_name("rerun_safely.py")
SOURCE_PATHS = (
    "runtime/core_v1/compiled_gui.py",
    "research/live_control/integrated_efficiency_compiled_adapter_v1.py",
    "research/live_control/integrated_efficiency_compiled_adapter_v2.py",
)


class SafeRerunTimeoutTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.package = self.root / "package"
        self.source = self.root / "source"
        self.output = self.root / "output"
        self.package.mkdir()
        self.source.mkdir()
        shutil.copyfile(WRAPPER, self.package / "rerun_safely.py")
        for relative in SOURCE_PATHS:
            path = self.source / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("# timeout fixture source\n", encoding="utf-8")

    def tearDown(self):
        self.temporary.cleanup()

    def invoke(self, run_id):
        return subprocess.run(
            [sys.executable, "-B", str(self.package / "rerun_safely.py"),
             "--source-root", str(self.source), "--output-root", str(self.output),
             "--run-id", run_id, "--timeout-seconds", "0.05"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False, timeout=10,
        )

    def test_candidate_timeout_writes_terminal_record_and_partial_output(self):
        (self.package / "executed-runner.py").write_text(
            "import time\nprint('candidate-started', flush=True)\ntime.sleep(2)\n",
            encoding="utf-8",
        )
        (self.package / "audit_raw.py").write_text("print('{}')\n", encoding="utf-8")

        result = self.invoke("candidate-timeout")

        run_dir = self.output / "candidate-timeout"
        metadata = json.loads((run_dir / "RUN.json").read_text(encoding="utf-8"))
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(metadata["candidate_status"], "timeout")
        self.assertEqual(metadata["auditor_status"], "not_run")
        self.assertIsNone(metadata["candidate_exit_code"])
        self.assertEqual((run_dir / "candidate-stdout.bin").read_bytes(), b"candidate-started\n")

    def test_auditor_timeout_writes_terminal_record_and_partial_output(self):
        (self.package / "executed-runner.py").write_text(
            "import json\nfrom pathlib import Path\n"
            "Path('raw-differential.json').write_text(json.dumps({'experiment_id':'fixture'}))\n",
            encoding="utf-8",
        )
        (self.package / "audit_raw.py").write_text(
            "import time\nprint('auditor-started', flush=True)\ntime.sleep(2)\n",
            encoding="utf-8",
        )

        result = self.invoke("auditor-timeout")

        run_dir = self.output / "auditor-timeout"
        metadata = json.loads((run_dir / "RUN.json").read_text(encoding="utf-8"))
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(metadata["candidate_status"], "completed")
        self.assertEqual(metadata["candidate_exit_code"], 0)
        self.assertEqual(metadata["auditor_status"], "timeout")
        self.assertIsNone(metadata["auditor_exit_code"])
        self.assertEqual((run_dir / "audit-stdout.bin").read_bytes(), b"auditor-started\n")


if __name__ == "__main__":
    unittest.main()
