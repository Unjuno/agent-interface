"""Run the frozen main-vs-candidate fake-X two-key comparison."""
import hashlib
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).parent
TEST = ROOT / "test_two_key_cleanup_order.py"
CASES = (("main", 1), ("candidate", 0))
FAILED = False

with tempfile.TemporaryDirectory(prefix="two-key-retry-order-") as tmp:
    tmp = Path(tmp)
    for name, expected_exit in CASES:
        case_dir = tmp / name
        case_dir.mkdir()
        source = ROOT / name / "input_owner_v12.py"
        shutil.copyfile(source, case_dir / "input_owner_v12.py")
        test = case_dir / TEST.name
        shutil.copyfile(TEST, test)
        print(f"SOURCE {name} sha256={hashlib.sha256(source.read_bytes()).hexdigest()}")
        for mode, flags in (("normal", []), ("optimized", ["-O"])):
            proc = subprocess.run(
                [sys.executable, *flags, "-B", str(test)],
                cwd=case_dir,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )
            print(f"=== {name} {mode}: exit={proc.returncode} expected={expected_exit} ===")
            print(proc.stdout.rstrip())
            if proc.returncode != expected_exit:
                FAILED = True

audit = subprocess.run(
    [sys.executable, "-B", str(ROOT / "audit_outcomes.py")],
    cwd=ROOT,
    text=True,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
)
print(f"=== independent audit: exit={audit.returncode} expected=0 ===")
print(audit.stdout.rstrip())
if audit.returncode != 0:
    FAILED = True

raise SystemExit(1 if FAILED else 0)
