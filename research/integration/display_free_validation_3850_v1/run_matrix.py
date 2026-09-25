"""One finite fresh engineering matrix, no GUI/input/model execution."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def digest(data):
    return hashlib.sha256(data).hexdigest()


def source_hashes():
    freeze = json.loads((HERE / "FREEZE.json").read_text())
    return {name: digest((ROOT / name).read_bytes()) for name in freeze["sources"]}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    output = args.output.resolve()
    freeze = json.loads((HERE / "FREEZE.json").read_text())
    before = source_hashes()
    if before != freeze["sources"]:
        raise RuntimeError("frozen source mismatch")
    cases = json.loads((HERE / "cases.json").read_text())["cases"]
    result = {"allocation": "display-free-3850-v7p2-01", "started_ns": time.monotonic_ns(),
              "python": sys.version, "source_hashes_before": before, "rows": [], "complete": False}
    (output / "START.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    for display in [None, ":59999"]:
        environment = "no_display" if display is None else "unusable_display"
        for case in cases:
            name = environment + "__" + case["id"]
            work = output / name
            work.mkdir()
            path = work / "input.json"
            if case["raw_text"] is not None:
                path.write_bytes(case["raw_text"].encode("utf-8"))
            initial = digest(path.read_bytes()) if path.exists() else None
            env = dict(os.environ)
            for key in ["DISPLAY", "WAYLAND_DISPLAY", "PYTHONPATH", "PYTHONSTARTUP"]:
                env.pop(key, None)
            if display is not None:
                env["DISPLAY"] = display
            cmd = [sys.executable, "-S", "-B", str(HERE / "probe.py"), str(path), str(work / "trace.json")]
            # Script execution uses the explicit repo root; -S excludes third-party site packages.
            env["PYTHONPATH"] = str(ROOT)
            try:
                proc = subprocess.run(cmd, cwd=ROOT, env=env, capture_output=True, timeout=10)
                row = {"id": name, "case": case["id"], "environment": environment, "argv": cmd,
                       "exit": proc.returncode, "stdout": proc.stdout.decode("utf-8"),
                       "stderr": proc.stderr.decode("utf-8"),
                       "input_sha256_before": initial,
                       "input_sha256_after": digest(path.read_bytes()) if path.exists() else None,
                       "trace": json.loads((work / "trace.json").read_text())}
            except Exception as error:
                result["stop"] = {"case": name, "type": type(error).__name__, "detail": str(error)}
                (output / "records.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
                raise
            (work / "stdout.txt").write_text(row["stdout"])
            (work / "stderr.txt").write_text(row["stderr"])
            result["rows"].append(row)
            (output / "records.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    result.update(complete=True, source_hashes_after=source_hashes(), ended_ns=time.monotonic_ns())
    (output / "records.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(json.dumps({"rows": len(result["rows"]), "complete": True}))


if __name__ == "__main__":
    main()
