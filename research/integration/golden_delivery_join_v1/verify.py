"""Offline retention audit and regression only; never reruns the formal matrix."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from unpack import unpack

STUDY = Path("research/integration/golden_delivery_join_v1")


def main():
    source = Path(__file__).resolve().parent
    with tempfile.TemporaryDirectory(prefix="golden-delivery-review-") as temporary:
        root = Path(temporary) / "restored"
        summary = unpack(source, root)
        study = root / STUDY
        result = subprocess.run([sys.executable, "-S", "-B", str(study / "audit.py"),
                                 str(study / "formal-01/RAW.jsonl"), "--root", str(root),
                                 "--freeze", str(study / "FREEZE.json"), "--controls"],
                                capture_output=True, timeout=30)
        if result.returncode != 0 or result.stderr or result.stdout != (study / "AUDIT.json").read_bytes():
            raise RuntimeError("retained audit did not reproduce exactly: " + repr(result))
        tests = subprocess.run([sys.executable, "-S", "-B", "-m", "unittest", "-v",
                                "runtime.cli_v1.test_golden_v3",
                                "runtime.cli_v1.test_golden_delivery_join"], cwd=root,
                               capture_output=True, timeout=30)
        if tests.returncode != 0:
            raise RuntimeError("retained regression tests failed: " + repr(tests))
        summary.update(audit_sha256=hashlib.sha256(result.stdout).hexdigest(),
                       decision=json.loads(result.stdout)["decision"],
                       audit_exit=result.returncode, regression_exit=tests.returncode,
                       formal_reruns=0)
        print(json.dumps(summary, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
