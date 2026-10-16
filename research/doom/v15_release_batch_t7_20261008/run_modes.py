"""Run T7 in normal and optimized modes and record deterministic outputs."""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUN = HERE / "run.py"
outputs = {}
for mode, flags in (("normal", []), ("optimized", ["-O"])):
    proc = subprocess.run([sys.executable, *flags, "-B", str(RUN)], capture_output=True, text=True)
    outputs[mode] = {"exit_code": proc.returncode, "stdout": proc.stdout.strip(), "stderr": proc.stderr.strip()}
    if proc.returncode != 0:
        raise SystemExit(f"{mode} failed: {proc.stderr}")
if outputs["normal"]["stdout"] != outputs["optimized"]["stdout"]:
    raise SystemExit("normal/optimized result mismatch")
result = json.loads(outputs["normal"]["stdout"])
(HERE / "normal.stdout").write_text(outputs["normal"]["stdout"] + "\n", encoding="utf-8")
(HERE / "optimized.stdout").write_text(outputs["optimized"]["stdout"] + "\n", encoding="utf-8")
(HERE / "RESULT.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
manifest = {}
for path in sorted(HERE.iterdir()):
    if path.is_file() and path.name != "SHA256SUMS.json":
        manifest[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
(HERE / "SHA256SUMS.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps({"normal_exit": outputs["normal"]["exit_code"], "optimized_exit": outputs["optimized"]["exit_code"],
                  "stdout_equal": True, "disposition": result["disposition"]}, sort_keys=True))
