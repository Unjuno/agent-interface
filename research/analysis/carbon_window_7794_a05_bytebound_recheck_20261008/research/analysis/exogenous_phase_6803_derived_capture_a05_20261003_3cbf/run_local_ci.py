"""Run every single-line Python command from the existing Analysis Index job.

Does not overwrite its workflow with the pinned provenance-test restore step;
records all failures instead. Actual Actions reproduces that setup independently.
"""
import hashlib
import json
from pathlib import Path
import shlex
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
WORKFLOW = REPO / ".github/workflows/analysis-index.yml"

if __name__ == "__main__":
    directory = ROOT / "local_ci"
    directory.mkdir()
    name, cwd, results = "", REPO, []
    for line in WORKFLOW.read_text().splitlines():
        if line.startswith("      - name: "):
            name, cwd = line.split("name: ", 1)[1], REPO
        elif line.startswith("        working-directory: "):
            cwd = REPO / line.split(": ", 1)[1]
        elif line.startswith("        run: python "):
            command = shlex.split(line.split("run: ", 1)[1])
            command[0] = sys.executable
            if "-B" not in command:
                command.insert(1, "-B")
            result = subprocess.run(command, cwd=cwd, capture_output=True, text=True)
            index = len(results)
            for stream in ("stdout", "stderr"):
                with (directory / f"{index:02}.{stream}.log").open("x") as target:
                    target.write(getattr(result, stream))
            results.append({"name": name, "command": command, "cwd": str(cwd.relative_to(REPO)),
                            "exit_code": result.returncode, "stdout": f"local_ci/{index:02}.stdout.log",
                            "stderr": f"local_ci/{index:02}.stderr.log"})
            print(name + ": exit=" + str(result.returncode), flush=True)
    with (ROOT / "LOCAL_CI.json").open("x") as target:
        json.dump({"workflow_sha256": hashlib.sha256(WORKFLOW.read_bytes()).hexdigest(),
                   "provenance_restore_step": "NOT reproduced; current workflow not overwritten locally",
                   "commands": results, "failed_commands": [r["name"] for r in results if r["exit_code"]]},
                  target, sort_keys=True, indent=2)
        target.write("\n")
    raise SystemExit(1 if any(r["exit_code"] for r in results) else 0)
