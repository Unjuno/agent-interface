#!/usr/bin/env python3
"""Single-launch frozen runner for Issue #7934 calibration successor A02."""
import gzip
import hashlib
import json
import pathlib
import subprocess
import sys

SRC = pathlib.Path(__file__).resolve().parent
OUT = pathlib.Path(sys.argv[1])
FROZEN = json.loads((SRC / "FROZEN.json").read_text(encoding="utf-8"))


def digest(data):
    return hashlib.sha256(data).hexdigest()


def sha(path):
    return digest(path.read_bytes())


def run_child(args, stdout_name, stderr_name):
    proc = subprocess.run(args, cwd=SRC, stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE, check=False)
    (OUT / stdout_name).write_bytes(proc.stdout)
    (OUT / stderr_name).write_bytes(proc.stderr)
    return proc


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for name, expected in FROZEN["source_sha256"].items():
        actual = sha(SRC / name)
        if actual != expected:
            (OUT / "terminal.json").write_text(json.dumps({
                "status": "STOP_FROZEN_SOURCE_MISMATCH", "file": name,
                "actual_sha256": actual, "expected_sha256": expected,
                "simulator_invocations": 0, "auditor_invocations": 0,
            }, sort_keys=True, indent=2) + "\n", encoding="utf-8")
            print("STOP_FROZEN_SOURCE_MISMATCH:%s" % name)
            return 2
    sim = run_child([sys.executable, str(SRC / "simulator.py"), str(OUT)],
                    "simulator.stdout.txt", "simulator.stderr.txt")
    if sim.returncode != 0:
        (OUT / "terminal.json").write_text(json.dumps({
            "status": "STOP_SIMULATOR_EXIT", "simulator_exit": sim.returncode,
            "simulator_invocations": 1, "auditor_invocations": 0,
            "retry_count": 0,
        }, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        print("STOP_SIMULATOR_EXIT:%d" % sim.returncode)
        return 1
    audit = run_child([sys.executable, str(SRC / "audit.py"),
                       str(OUT / "raw_observations.jsonl"),
                       str(OUT / "candidate_result.json"), str(OUT)],
                      "auditor.stdout.txt", "auditor.stderr.txt")
    raw = (OUT / "raw_observations.jsonl").read_bytes()
    candidate = (OUT / "candidate_result.json").read_bytes()
    lines = raw.splitlines(keepends=True)
    chunk_names = []
    for offset in range(0, len(lines), 512):
        index = offset // 512
        name = "raw/part-%02d.jsonl.gz" % index
        chunk = b"".join(lines[offset:offset + 512])
        path = OUT / name
        path.parent.mkdir(parents=True, exist_ok=True)
        packed = gzip.compress(chunk, mtime=0)
        path.write_bytes(packed)
        chunk_names.append({"path": name, "rows": min(512, len(lines) - offset),
                            "bytes": len(packed), "sha256": digest(packed),
                            "raw_bytes": len(chunk), "raw_sha256": digest(chunk)})
    candidate_gz = gzip.compress(candidate, mtime=0)
    (OUT / "candidate_result.json.gz").write_bytes(candidate_gz)
    audit_path = OUT / "independent_audit.json"
    audit_report = json.loads(audit_path.read_text(encoding="utf-8")) if audit_path.exists() else {}
    status = audit_report.get("status", "FAIL_AUDIT") if audit.returncode == 0 else "FAIL_AUDIT"
    terminal = {
        "allocation": "7934-T0-A02", "status": status,
        "simulator_exit": sim.returncode, "auditor_exit": audit.returncode,
        "simulator_invocations": 1, "auditor_invocations": 1,
        "formal_container_launches": 1, "retry_count": 0,
        "runtime": sys.version, "engine": "WSLc 3.0.1.0",
        "image": "python@sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016",
        "network": "none", "configured_cpus": 1,
        "cpu_enforcement_measured": False,
        "source_mount": "read-only", "output_mount": "read-write",
        "raw_observations": len(lines), "raw_sha256": digest(raw),
        "candidate_result_sha256": digest(candidate),
        "audit_report_sha256": sha(audit_path) if audit_path.exists() else None,
    }
    (OUT / "terminal.json").write_text(json.dumps(terminal, sort_keys=True, indent=2) + "\n",
                                         encoding="utf-8")
    manifest = {
        "schema": "issue7934-t0-a02-formal-transport-v1",
        "raw": {"rows": len(lines), "bytes": len(raw), "sha256": digest(raw),
                "parts": chunk_names},
        "candidate_result": {"uncompressed_bytes": len(candidate),
                             "uncompressed_sha256": digest(candidate),
                             "gzip_bytes": len(candidate_gz),
                             "gzip_sha256": digest(candidate_gz)},
        "streams": {name: {"bytes": len((OUT / name).read_bytes()),
                            "sha256": sha(OUT / name)} for name in (
                                "simulator.stdout.txt", "simulator.stderr.txt",
                                "auditor.stdout.txt", "auditor.stderr.txt")},
        "terminal_sha256": sha(OUT / "terminal.json"),
    }
    (OUT / "FORMAL_MANIFEST.json").write_text(
        json.dumps(manifest, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": status, "simulator_exit": sim.returncode,
                      "auditor_exit": audit.returncode, "observations": len(lines),
                      "raw_sha256": digest(raw), "terminal_sha256": manifest["terminal_sha256"]},
                     sort_keys=True))
    return audit.returncode


if __name__ == "__main__":
    raise SystemExit(main())
