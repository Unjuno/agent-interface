#!/usr/bin/env python3
"""One-shot isolated Codex CLI invocation; raw data is kept locally ignored."""
from pathlib import Path
import hashlib
import json
import subprocess

ROOT = Path(__file__).resolve().parent
PRIVATE = ROOT / "private"
LOCK = PRIVATE / "G23_ATTEMPTED.lock"
if LOCK.exists():
    raise SystemExit("one-shot marker exists; refusing another inference")
PRIVATE.mkdir(exist_ok=True)
with LOCK.open("x") as f:
    f.write("attempted\n")

prompt = (ROOT / "PROMPT.txt").read_text()
command = [
    "codex", "exec", "--json", "--ephemeral", "--ignore-user-config",
    "--skip-git-repo-check", "-C", "/tmp", "-s", "read-only",
    "-m", "gpt-6.1-sol", "-c", "model_reasoning_effort=medium",
]
for name in ("repair-01.png", "repair-02.png", "repair-03.png", "repair-04.png"):
    command += ["--image", str((ROOT / "input" / name).resolve())]
command.append(prompt)
proc = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
stdout = proc.stdout
stderr = proc.stderr
(PRIVATE / "raw.stdout.jsonl").write_bytes(stdout)
(PRIVATE / "raw.stderr").write_bytes(stderr)
receipt = {
    "exit_code": proc.returncode,
    "stdout_sha256": hashlib.sha256(stdout).hexdigest(),
    "stderr_sha256": hashlib.sha256(stderr).hexdigest(),
    "stdout_bytes": len(stdout),
    "stderr_bytes": len(stderr),
}
(PRIVATE / "local_receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
print(json.dumps({"exit_code": proc.returncode, "stdout_bytes": len(stdout), "stderr_bytes": len(stderr)}))
