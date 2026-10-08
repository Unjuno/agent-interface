"""One-shot candidate then raw-only audit orchestrator; no retries or substitutions."""
import argparse
import hashlib
import json
import socket
import subprocess
import sys
from pathlib import Path


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run(argv):
    p = subprocess.run(argv, text=True, capture_output=True, check=False)
    return {"argv": argv, "exit_code": p.returncode, "stdout": p.stdout, "stderr": p.stderr}


def main():
    parser = argparse.ArgumentParser()
    for name in ("input", "truth", "candidate", "audit", "freeze", "out"):
        parser.add_argument("--" + name, required=True)
    args = parser.parse_args()
    out = Path(args.out)
    raw, audit_out = out / "candidate.raw.jsonl", out / "audit.json"
    if raw.exists() or audit_out.exists():
        raise SystemExit("STOP_OUTPUT_PATH_PREEXISTS")
    freeze = json.loads(Path(args.freeze).read_text(encoding="utf-8"))
    frozen_paths = {
        "make_fixture.py": Path(args.candidate).with_name("make_fixture.py"),
        "candidate.py": Path(args.candidate),
        "audit.py": Path(args.audit),
        "input.json": Path(args.input),
        "truth.json": Path(args.truth),
        "run_formal.py": Path(__file__),
    }
    expected = {**freeze["source_sha256"], **freeze["input_sha256"]}
    for name, path in frozen_paths.items():
        if expected.get(name) != sha(path):
            raise SystemExit("STOP_FROZEN_SHA_MISMATCH:" + name)
    if freeze.get("status") != "FROZEN_PRE_FORMAL":
        raise SystemExit("STOP_FREEZE_STATUS")
    candidate_run = run([sys.executable, "-B", args.candidate, "--input", args.input, "--output", str(raw)])
    auditor_run = None
    if candidate_run["exit_code"] == 0 and raw.exists():
        auditor_run = run([sys.executable, "-B", args.audit, "--input", args.input,
                           "--truth", args.truth, "--raw", str(raw), "--output", str(audit_out)])
    result = {
        "allocation_id": "INTERMITTENT-IDENTITY-SWITCH-6061-T1-20261002-01",
        "candidate_invocations": 1, "auditor_invocations": 1 if auditor_run is not None else 0,
        "retries": 0, "candidate": candidate_run, "auditor": auditor_run,
        "image_id": freeze["image"]["image_id"],
        "container_hostname": socket.gethostname(),
        "sha256": {name: sha(path) for name, path in (
            ("input", args.input), ("truth", args.truth), ("candidate", args.candidate), ("audit", args.audit))},
        "freeze_sha256": sha(args.freeze),
        "raw_sha256": sha(raw) if raw.exists() else None,
        "audit_sha256": sha(audit_out) if audit_out.exists() else None,
        "scope": "synthetic commanded motor ticks only; no live motor, X11, GUI, model, game, network, or user data",
    }
    (out / "RUN.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"candidate_exit": candidate_run["exit_code"],
                      "auditor_exit": None if auditor_run is None else auditor_run["exit_code"],
                      "retries": 0, "raw_sha256": result["raw_sha256"],
                      "audit_sha256": result["audit_sha256"]}, sort_keys=True))
    if candidate_run["exit_code"] != 0 or auditor_run is None or auditor_run["exit_code"] != 0:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
