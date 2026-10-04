import hashlib
import json
import platform
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def now():
    return datetime.now(timezone.utc).isoformat()


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    freeze = json.loads((ROOT / "FREEZE.json").read_text(encoding="utf-8"))
    for filename, expected in freeze["sources"].items():
        if digest(ROOT / filename) != expected:
            raise RuntimeError("source mismatch: " + filename)
    output = ROOT / "run01"
    output.mkdir(exist_ok=False)
    receipt = {"allocation": freeze["allocation"], "started_at": now(), "python": sys.version, "platform": platform.platform(), "phases": [], "sources": freeze["sources"]}
    commands = [("candidate", [sys.executable, "-B", "run_candidate.py", str(output / "candidate-raw.json")]),
                ("audit", [sys.executable, "-B", "auditor.py", str(output / "candidate-raw.json"), freeze["sources"]["retained_candidate.py"], str(output / "audit.json")])]
    for name, command in commands:
        phase = {"name": name, "argv": command, "started_at": now()}
        started = time.perf_counter_ns()
        try:
            proc = subprocess.run(command, cwd=ROOT, capture_output=True, timeout=20)
            phase.update(exit_code=proc.returncode, timed_out=False)
            stdout, stderr = proc.stdout, proc.stderr
        except subprocess.TimeoutExpired as exc:
            phase.update(exit_code=None, timed_out=True)
            stdout, stderr = exc.stdout or b"", exc.stderr or b""
        phase.update(ended_at=now(), elapsed_ns=time.perf_counter_ns() - started)
        for suffix, data in (("stdout", stdout), ("stderr", stderr)):
            with (output / f"{name}.{suffix}.txt").open("xb") as stream:
                stream.write(data)
        receipt["phases"].append(phase)
        if phase["exit_code"] != 0:
            break
    receipt["ended_at"] = now()
    receipt["files"] = {p.name: digest(p) for p in output.iterdir() if p.is_file()}
    total_bytes = sum(p.stat().st_size for p in output.iterdir() if p.is_file())
    receipt["output_bytes_before_receipt"] = total_bytes
    receipt["output_bound_passed"] = total_bytes < 1024 * 1024
    with (output / "RUN.json").open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(receipt, stream, sort_keys=True, indent=2)
        stream.write("\n")
    print(json.dumps(receipt, sort_keys=True))
    return 0 if len(receipt["phases"]) == 2 and all(p["exit_code"] == 0 for p in receipt["phases"]) and receipt["output_bound_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
