from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
commands = {
    "tests": [sys.executable, "-m", "unittest", "-v", "test_point_click_composition.py"],
    "pycompile": [sys.executable, "-m", "py_compile", "candidate.py", "test_point_click_composition.py", "run.py", "audit.py"],
}
records = {}
for name, command in commands.items():
    result = subprocess.run(command, cwd=HERE, capture_output=True, text=True, encoding="utf-8")
    stdout_path, stderr_path = f"{name}.stdout.txt", f"{name}.stderr.txt"
    (HERE / stdout_path).write_text(result.stdout, encoding="utf-8")
    (HERE / stderr_path).write_text(result.stderr, encoding="utf-8")
    records[name] = {"command": command, "exit_code": result.returncode,
                     "stdout_path": stdout_path, "stderr_path": stderr_path}
(HERE / "RUNS.json").write_text(json.dumps(records, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps({name: row["exit_code"] for name, row in records.items()}, sort_keys=True))
if any(row["exit_code"] for row in records.values()):
    raise SystemExit(1)
