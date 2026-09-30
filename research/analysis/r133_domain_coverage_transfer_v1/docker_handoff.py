"""Host-to-Docker runner for frozen, hash-checked source payloads."""

import json
import pathlib
import subprocess
import sys

from frozen_sources import BASE_COMMIT, SOURCES

IMAGE = "r133-coverage-t0-03:local"
ALLOCATION = "t0-03"


def build_payload(repository):
    resolved_base = subprocess.run(
        ["git", "rev-parse", BASE_COMMIT], cwd=repository,
        check=True, capture_output=True, text=True,
    ).stdout.strip()
    if resolved_base != BASE_COMMIT:
        raise ValueError("frozen base commit mismatch")
    sources = {}
    for name, (source_path, blob) in SOURCES.items():
        resolved_blob = subprocess.run(
            ["git", "rev-parse", f"{BASE_COMMIT}:{source_path}"], cwd=repository,
            check=True, capture_output=True, text=True,
        ).stdout.strip()
        if resolved_blob != blob:
            raise ValueError("frozen path/blob mismatch:" + name)
        raw = subprocess.run(
            ["git", "cat-file", "blob", blob], cwd=repository,
            check=True, capture_output=True,
        ).stdout
        sources[name] = raw.decode("utf-8")
    return json.dumps({"base_commit": BASE_COMMIT, "sources": sources}, sort_keys=True, separators=(",", ":")).encode()


def _docker_mount(path):
    return str(path.resolve()).replace("\\", "/")


def docker_command(bundle):
    return [
        "docker", "run", "--rm", "-i", "--network", "none", "--read-only",
        "--tmpfs", "/tmp:rw,noexec,nosuid,size=64m",
        "--mount", f"type=bind,src={_docker_mount(bundle)},dst=/work",
        "--workdir", "/work", IMAGE,
    ]


def run_allocation(repository, bundle):
    repository = pathlib.Path(repository).resolve()
    bundle = pathlib.Path(bundle).resolve()
    output = bundle / "results" / ALLOCATION
    if output.exists():
        raise SystemExit("STOP_OUTPUT_ALREADY_EXISTS")
    payload = build_payload(repository)
    shared = docker_command(bundle)
    candidate = subprocess.run(shared + ["run_once.py", "--stdin", ALLOCATION], input=payload,
                               capture_output=True, check=False)
    (bundle / "results" / f"{ALLOCATION}-container-run.log").write_bytes(candidate.stdout + candidate.stderr)
    if candidate.returncode != 0:
        raise SystemExit("STOP_CANDIDATE_CONTAINER:" + str(candidate.returncode))
    audit = subprocess.run(
        shared + ["audit.py", "--stdin", f"/work/results/{ALLOCATION}/candidate.json"],
        input=payload, capture_output=True, check=False,
    )
    (bundle / "results" / f"{ALLOCATION}-audit-container.log").write_bytes(audit.stdout + audit.stderr)
    if audit.returncode != 0:
        raise SystemExit("AUDIT_FAILED:" + str(audit.returncode))
    return {"candidate_stdout": candidate.stdout.decode("utf-8"), "audit_stdout": audit.stdout.decode("utf-8")}


def main():
    bundle = pathlib.Path(__file__).resolve().parent
    repository = bundle.parents[2]
    result = run_allocation(repository, bundle)
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
