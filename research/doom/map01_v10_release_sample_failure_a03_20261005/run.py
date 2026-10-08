"""Replay the frozen V10 A03 fake-X tests without changing retained evidence."""
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
expected = {"baseline": 1, "candidate": 0}
failed = False

for variant in ("baseline", "candidate"):
    for mode, flags in (("normal", []), ("optimized", ["-O"])):
        with tempfile.TemporaryDirectory(prefix="v10-a03-") as temp:
            temp = Path(temp)
            for name in ("input_owner_v10.py", "test_input_owner_v10_release_retry.py"):
                (temp / name).write_bytes((ROOT / "source" / variant / name).read_bytes())
            command = [sys.executable, *flags, "-m", "unittest", "-v",
                       "test_input_owner_v10_release_retry.py"]
            run = subprocess.run(command, cwd=temp, text=True, capture_output=True)
            passed = run.returncode == expected[variant]
            failed |= not passed
            stream = run.stdout + run.stderr
            summary = next((line for line in reversed(stream.splitlines())
                            if line.startswith(("Ran ", "FAILED ", "OK"))), "no test summary")
            print(f"{variant} {mode}: exit={run.returncode} {summary} "
                  f"({'expected' if passed else 'unexpected'})")
            if not passed:
                print(stream)

raise SystemExit(1 if failed else 0)
