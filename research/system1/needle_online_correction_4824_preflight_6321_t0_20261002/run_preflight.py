"""One-shot data construction then independent raw audit; never trains a model."""
import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run(argv):
    result = subprocess.run(argv, text=True, capture_output=True, check=False)
    return {"argv": argv, "exit_code": result.returncode,
            "stdout": result.stdout, "stderr": result.stderr}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--package", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    package, output = Path(args.package), Path(args.output)
    freeze = json.loads((package / "FREEZE.json").read_text(encoding="utf-8"))
    frozen = {name: package / name for name in (
        "PLAN.md", "config.json", "make_data.py", "audit_data.py",
        "test_preflight.py", "run_preflight.py")}
    mismatches = {name: {"expected": digest, "actual": sha(frozen[name])}
                  for name, digest in freeze["sha256"].items()
                  if name not in frozen or sha(frozen[name]) != digest}
    if freeze.get("status") != "FROZEN_PRE_FORMAL" or mismatches:
        raise SystemExit("STOP_FROZEN_SOURCE_MISMATCH:" + json.dumps(mismatches, sort_keys=True))
    raw, audit_path = output / "data.json", output / "audit.json"
    run_path = output / "RUN.json"
    if any(path.exists() for path in (raw, audit_path, run_path)):
        raise SystemExit("STOP_OUTPUT_PATH_PREEXISTS")
    generator = run([sys.executable, "-B", str(package / "make_data.py"),
                     "--config", str(package / "config.json"), "--output", str(raw)])
    auditor = None
    if generator["exit_code"] == 0 and raw.exists():
        auditor = run([sys.executable, "-B", str(package / "audit_data.py"),
                       str(raw), str(audit_path)])
    audit = json.loads(audit_path.read_text(encoding="utf-8")) if audit_path.exists() else None
    receipt = {
        "allocation": freeze["allocation"], "main_sha": freeze["main_sha"],
        "image_id": freeze["image_id"], "platform": freeze["platform"],
        "generator_invocations": 1, "auditor_invocations": 1 if auditor else 0,
        "retries": 0, "generator": generator, "auditor": auditor,
        "raw_sha256": sha(raw) if raw.exists() else None,
        "audit_sha256": sha(audit_path) if audit_path.exists() else None,
        "freeze_sha256": sha(package / "FREEZE.json"),
        "decision": None if audit is None else audit["status"],
        "errors": None if audit is None else audit["errors"],
        "mutation_rejections": None if audit is None else sum(x["rejected"] for x in audit["mutations"]),
        "scope": "deterministic dataset construction/label audit only; no model, optimizer, CUDA, GPU, GUI, or network"
    }
    run_path.write_text(json.dumps(receipt, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"decision": receipt["decision"], "errors": receipt["errors"],
                      "mutation_rejections": receipt["mutation_rejections"]}, sort_keys=True))
    if generator["exit_code"] != 0 or auditor is None or auditor["exit_code"] != 0 or audit["errors"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
