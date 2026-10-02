"""One-shot host runner for the frozen #5531 T6-E1 finite experiment."""
import argparse
import hashlib
import json
import os
import platform
import subprocess
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def invoke(argv):
    process = subprocess.Popen(argv, cwd=HERE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               text=True, env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
    try:
        stdout, stderr = process.communicate(timeout=20)
        return {"argv": argv, "pid": process.pid, "returncode": process.returncode,
                "stdout": stdout, "stderr": stderr, "timed_out": False}
    except subprocess.TimeoutExpired:
        process.kill()
        stdout, stderr = process.communicate()
        return {"argv": argv, "pid": process.pid, "returncode": process.returncode,
                "stdout": stdout, "stderr": stderr, "timed_out": True}


def run(results_dir):
    results = Path(results_dir).resolve()
    results.mkdir(parents=True, exist_ok=False)
    manifest = json.loads((HERE / "SOURCE_MANIFEST.json").read_text(encoding="utf-8"))
    checked = {}
    for name, expected in manifest["sources"].items():
        actual = sha256(HERE / name)
        checked[name] = {"expected": expected, "actual": actual, "matches": actual == expected}
    if not all(item["matches"] for item in checked.values()):
        raise SystemExit("frozen source manifest mismatch; no candidate invocation")
    raw = results / "raw.jsonl"
    candidate = invoke([sys.executable, "-B", "candidate.py", "--raw", str(raw)])
    (results / "candidate.stdout.txt").write_text(candidate["stdout"], encoding="utf-8")
    (results / "candidate.stderr.txt").write_text(candidate["stderr"], encoding="utf-8")
    auditor = None
    if candidate["returncode"] == 0:
        auditor = invoke([sys.executable, "-B", "audit.py", str(raw),
                          str(results / "audit.json"), str(HERE / "freeze.json")])
        (results / "auditor.stdout.txt").write_text(auditor["stdout"], encoding="utf-8")
        (results / "auditor.stderr.txt").write_text(auditor["stderr"], encoding="utf-8")
    audit = json.loads((results / "audit.json").read_text(encoding="utf-8")) if (results / "audit.json").is_file() else {}
    execution = {
        "schema": "failure-detector-async-bound-execution-v1",
        "base_main": manifest["base_main"],
        "source_manifest_sha256": sha256(HERE / "SOURCE_MANIFEST.json"),
        "infrastructure_preflight_sha256": sha256(HERE / "infrastructure-preflight.json"),
        "source_checks": checked,
        "container_used": False,
        "python_version": platform.python_version(),
        "host_platform": platform.platform(),
        "candidate_invocations": 1,
        "candidate_pid": candidate["pid"],
        "candidate_argv": candidate["argv"],
        "candidate_returncode": candidate["returncode"],
        "candidate_timed_out": candidate["timed_out"],
        "auditor_invocations": int(auditor is not None),
        "auditor_pid": auditor["pid"] if auditor else None,
        "auditor_argv": auditor["argv"] if auditor else None,
        "auditor_returncode": auditor["returncode"] if auditor else None,
        "auditor_timed_out": auditor["timed_out"] if auditor else False,
        "disposition": audit.get("status", "STOP_NO_AUDIT"),
        "raw_sha256": sha256(raw) if raw.is_file() else None,
    }
    (results / "execution.json").write_text(json.dumps(execution, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(execution, sort_keys=True))
    if candidate["returncode"] != 0 or auditor is None or auditor["returncode"] != 0:
        return 1
    return 0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", required=True)
    args = parser.parse_args()
    raise SystemExit(run(args.results))


if __name__ == "__main__":
    main()
