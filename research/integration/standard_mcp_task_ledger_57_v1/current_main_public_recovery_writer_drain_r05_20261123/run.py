from datetime import datetime, timezone
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
TEST = "runtime.cli_v1.test_mcp_supervised_win32.SupervisedWin32MCPTests.test_public_compiled_caller_joins_exact_result_query_and_task_oracle"
RUNS = (("normal", ["-m", "unittest", "-v", TEST]),
        ("optimized", ["-O", "-m", "unittest", "-v", TEST]))
failed = False
for name, args in RUNS:
    (ROOT / f"{name}.started_utc.txt").write_text(
        datetime.now(timezone.utc).isoformat() + "\n", encoding="ascii")
    try:
        result = subprocess.run([sys.executable, *args], cwd=ROOT.parents[3],
                                capture_output=True, timeout=240)
        code, stdout, stderr = result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired as error:
        code = 124
        stdout = error.stdout or b""
        stderr = error.stderr or b""
        stderr += b"\nparent harness timeout after 240 seconds\n"
    (ROOT / f"{name}.stdout").write_bytes(stdout)
    (ROOT / f"{name}.stderr").write_bytes(stderr)
    (ROOT / f"{name}.exit").write_text(f"{code}\n", encoding="ascii")
    (ROOT / f"{name}.finished_utc.txt").write_text(
        datetime.now(timezone.utc).isoformat() + "\n", encoding="ascii")
    print(f"{name}: exit={code}; stdout_bytes={len(stdout)}; stderr_bytes={len(stderr)}")
    failed |= code != 0
sys.exit(1 if failed else 0)