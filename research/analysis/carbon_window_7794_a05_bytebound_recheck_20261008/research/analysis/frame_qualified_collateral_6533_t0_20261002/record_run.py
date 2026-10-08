#!/usr/bin/env python3
"""Collect execution receipts after the one-shot container allocation."""

import datetime as dt
import json
import platform
import subprocess
import sys
from pathlib import Path


def command(args):
    return subprocess.run(args, capture_output=True, text=True, check=False)


def main(out_dir, candidate_rc, auditor_rc, started_utc):
    out = Path(out_dir)
    image = "python:3.12-slim@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f"
    inspect = command(["docker", "--context", "orbstack", "image", "inspect", image,
                       "--format", "{{.Id}} {{.Os}}/{{.Architecture}}"])
    info = command(["docker", "--context", "orbstack", "info", "--format",
                    "{{.OSType}} {{.Architecture}} {{.NCPU}} {{.MemTotal}} {{.CgroupVersion}} {{.KernelVersion}}"])
    latest_main = command(["git", "-C", str(out.parents[1]), "rev-parse", "origin/main"])
    head = command(["git", "-C", str(out.parents[1]), "rev-parse", "HEAD"])
    context = command(["docker", "context", "show"])
    cids = {}
    cleanup = {}
    for role in ("candidate", "auditor"):
        cid_file = out / f"{role}.cid"
        cid = cid_file.read_text().strip() if cid_file.exists() else ""
        cids[role] = cid
        if cid:
            check = command(["docker", "--context", "orbstack", "ps", "-a", "--no-trunc",
                             "--filter", f"id={cid}", "--format", "{{.ID}} {{.Names}} {{.Status}}"])
            cleanup[role] = {"cid_absent_after_rm": not check.stdout.strip(),
                             "inspect_output": check.stdout.strip()}
        else:
            cleanup[role] = {"cid_absent_after_rm": False, "reason": "cid file missing"}
    now = dt.datetime.now(dt.timezone.utc).isoformat()
    run = {
        "schema": "issue6533-run-v1",
        "allocation_id": "frame-qualified-collateral-6533-t0-20261002-01",
        "recorded_at_utc": now,
        "started_at_utc": started_utc,
        "host": {"os": platform.platform(), "python": platform.python_version()},
        "git": {"head": head.stdout.strip(), "origin_main_observed_after_run": latest_main.stdout.strip()},
        "engine": {"context": context.stdout.strip(), "info_summary": info.stdout.strip(),
                   "image_inspect": inspect.stdout.strip()},
        "containers": {"candidate": cids["candidate"], "auditor": cids["auditor"],
                       "cleanup_readback": cleanup},
        "commands": {"candidate": (out / "candidate.command.txt").read_text().strip(),
                     "auditor": (out / "auditor.command.txt").read_text().strip()},
        "resource_configuration": {"cpus": 1, "memory_bytes": 536870912, "pids": 64,
                                  "network": "none", "root_read_only": True,
                                  "tmpfs": "/tmp:rw,noexec,nosuid,size=16m",
                                  "cap_drop": "ALL", "no_new_privileges": True,
                                  "source_mount": "read-only", "limits_enforcement_claim": False},
        "exit_codes": {"candidate": int(candidate_rc), "auditor": int(auditor_rc)},
        "retries": 0,
    }
    (out / "RUN.json").write_text(json.dumps(run, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
