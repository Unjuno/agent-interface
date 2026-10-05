#!/usr/bin/env python3
"""Single-launch frozen runner; preserves exact child streams and audit output."""
import hashlib
import json
import pathlib
import subprocess
import sys

SRC = pathlib.Path(__file__).resolve().parent
OUT = pathlib.Path(sys.argv[1])
FROZEN = json.loads((SRC / "FROZEN.json").read_text(encoding="utf-8"))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for name, expected in FROZEN["source_sha256"].items():
        actual = digest(SRC / name)
        if actual != expected:
            raise SystemExit("STOP_FROZEN_SOURCE_MISMATCH:%s:%s" % (name, actual))
    sim = subprocess.run([sys.executable, str(SRC / "simulator.py"), str(OUT)],
                         cwd=SRC, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                         check=False)
    (OUT / "simulator.stdout.txt").write_bytes(sim.stdout)
    (OUT / "simulator.stderr.txt").write_bytes(sim.stderr)
    if sim.returncode != 0:
        (OUT / "terminal.json").write_text(json.dumps({
            "status": "STOP_SIMULATOR_EXIT", "simulator_exit": sim.returncode,
            "auditor_invocations": 0,
        }, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        print("STOP_SIMULATOR_EXIT:%d" % sim.returncode)
        return 1
    audit = subprocess.run([
        sys.executable, str(SRC / "audit.py"),
        str(OUT / "raw_observations.jsonl"),
        str(OUT / "candidate_result.json"), str(OUT),
    ], cwd=SRC, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    (OUT / "auditor.stdout.txt").write_bytes(audit.stdout)
    (OUT / "auditor.stderr.txt").write_bytes(audit.stderr)
    audit_json = OUT / "independent_audit.json"
    terminal = {
        "status": "PASS_METHOD_SCOPED" if audit.returncode == 0 else "FAIL_AUDIT",
        "simulator_exit": sim.returncode,
        "auditor_exit": audit.returncode,
        "simulator_invocations": 1,
        "auditor_invocations": 1,
        "retry_count": 0,
        "audit_report_sha256": digest(audit_json) if audit_json.exists() else None,
        "runtime": sys.version,
        "configured_cpus": 1,
        "cpu_enforcement_measured": False,
        "network": "none",
        "formal_container_launches": 1,
    }
    (OUT / "terminal.json").write_text(json.dumps(terminal, sort_keys=True, indent=2) + "\n",
                                         encoding="utf-8")
    print(json.dumps({"status": terminal["status"],
                      "simulator_exit": sim.returncode,
                      "auditor_exit": audit.returncode,
                      "audit_report_sha256": terminal["audit_report_sha256"]},
                     sort_keys=True))
    return audit.returncode


if __name__ == "__main__":
    raise SystemExit(main())
