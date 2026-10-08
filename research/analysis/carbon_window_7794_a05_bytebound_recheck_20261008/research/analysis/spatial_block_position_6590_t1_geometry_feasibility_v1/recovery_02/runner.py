from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path


SOURCE_FILES = ("README.md", "PROTOCOL.md", "runner.py", "../test_runner.py",
                "../FREEZE.json", "../FREEZE.sha256", "../candidate.py", "../auditor.py",
                "../Dockerfile", "../preformal/README.md", "../preformal/host_candidate.json",
                "../results/preflight-01/STOP.json",
                "../../../../.github/workflows/analysis-index.yml")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def invoke(argv):
    return subprocess.run(argv, text=True, capture_output=True, check=False)


def runtime_settings(freeze: dict):
    environment = freeze["environment"]
    return environment, environment["resource_limits"]


def verify(root: Path, freeze: dict):
    if set(freeze.get("source_sha256", {})) != set(SOURCE_FILES):
        raise ValueError("frozen source inventory mismatch")
    sidecar = root / "FREEZE.sha256"
    if sha256(root / "FREEZE.json") != sidecar.read_text(encoding="ascii").split()[0]:
        raise ValueError("recovery freeze sidecar mismatch")
    for relative, expected in freeze["source_sha256"].items():
        if sha256((root / relative).resolve()) != expected:
            raise ValueError(f"recovery source hash mismatch: {relative}")
    package = root.parent
    parent_side = package / "FREEZE.sha256"
    if sha256(package / "FREEZE.json") != parent_side.read_text(encoding="ascii").split()[0]:
        raise ValueError("allocation 01 freeze sidecar mismatch")
    if sha256(package / "preformal" / "host_candidate.json") != freeze["preformal_candidate_sha256"]:
        raise ValueError("known host construction output hash mismatch")
    env = freeze["environment"]
    image_result = invoke(["docker", "image", "inspect", env["image"]])
    if image_result.returncode:
        raise ValueError(f"frozen image unavailable: {image_result.stderr.strip()}")
    image = json.loads(image_result.stdout)[0]
    if (image.get("Id") != env["image_id"] or image.get("Os") != "linux"
            or image.get("Architecture") != "arm64"
            or env["image_manifest_digest"] not in image.get("RepoDigests", [])):
        raise ValueError("recovery image identity/platform mismatch")


def docker_create(image: str, name: str, command: list[str], mounts: list[str], resources: dict) -> list[str]:
    argv = ["docker", "create", "--name", name, "--platform", "linux/arm64", "--network", "none",
            "--cpus", str(resources["cpus"]), "--memory", resources["memory"],
            "--pids-limit", str(resources["pids"]), "--read-only", "--cap-drop", "ALL",
            "--security-opt", "no-new-privileges"]
    for mount in mounts:
        argv.extend(["--mount", mount])
    argv.extend([image, *command])
    return argv


def create_container(image: str, name: str, command: list[str], mounts: list[str], resources: dict):
    argv = docker_create(image, name, command, mounts, resources)
    result = invoke(argv)
    return {"container_id": result.stdout.strip() if result.returncode == 0 else None,
            "exit_code": result.returncode, "create_command": argv,
            "create_stderr": result.stderr, "created": result.returncode == 0}


def start_capture(container: dict, destination: Path, label: str):
    container_id = container["container_id"]
    result = invoke(["docker", "start", "--attach", container_id])
    stdout_path = destination / f"{label}.stdout.txt"
    stderr_path = destination / f"{label}.stderr.txt"
    stdout_path.write_text(result.stdout, encoding="utf-8")
    stderr_path.write_text(result.stderr, encoding="utf-8")
    inspected = invoke(["docker", "inspect", container_id])
    inspect_data = json.loads(inspected.stdout)[0] if inspected.returncode == 0 else None
    container.update({"start_command": ["docker", "start", "--attach", container_id],
                      "exit_code": result.returncode,
                      "started_at": inspect_data["State"].get("StartedAt") if inspect_data else None,
                      "finished_at": inspect_data["State"].get("FinishedAt") if inspect_data else None,
                      "state": inspect_data["State"] if inspect_data else None,
                      "host_config": inspect_data["HostConfig"] if inspect_data else None,
                      "inspect_error": inspected.stderr if inspected.returncode else None,
                      "stdout_sha256": sha256(stdout_path), "stderr_sha256": sha256(stderr_path)})
    return container


def capture_hashes(output: Path):
    return {str(path.relative_to(output)): sha256(path)
            for path in sorted(output.rglob("*")) if path.is_file()}


def save_record(output: Path, record: dict):
    record["artifact_sha256"] = capture_hashes(output)
    (output / "RUN_RECORD.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    freeze = json.loads((root / "FREEZE.json").read_text(encoding="utf-8"))
    verify(root, freeze)
    package = root.parent
    output = package / "results" / "replication-02"
    if output.exists():
        raise FileExistsError("recovery output exists; this allocation is one-shot")
    candidate_output, audit_output = output / "candidate", output / "audit"
    candidate_output.mkdir(parents=True)
    audit_output.mkdir(parents=True)
    env, resources = runtime_settings(freeze)
    source_mount = f"type=bind,src={package},dst=/package,readonly"
    candidate_create = create_container(env["image"], freeze["candidate_container_name"],
        ["python", "/package/candidate.py", "--out", "/out/raw.json"],
        [source_mount, f"type=bind,src={candidate_output},dst=/out"], resources)
    auditor_create = None
    if candidate_create["created"]:
        auditor_create = create_container(env["image"], freeze["auditor_container_name"],
            ["python", "/package/auditor.py", "--raw", "/raw/raw.json", "--out", "/out/AUDIT.json"],
            [source_mount, f"type=bind,src={candidate_output},dst=/raw,readonly",
             f"type=bind,src={audit_output},dst=/out"], resources)
    if not candidate_create["created"] or not auditor_create or not auditor_create["created"]:
        cleanup = []
        for item in (candidate_create, auditor_create):
            if item and item.get("container_id"):
                cleanup.append(invoke(["docker", "rm", item["container_id"]]).stdout.strip())
        record = {"schema": "spatial-block-6590-t1-geometry-recovery-run-record-v1",
                  "allocation": freeze["allocation"], "status": "STOP_PRELAUNCH_CONTAINER_CREATE",
                  "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
                  "freeze_sha256": sha256(root / "FREEZE.json"), "candidate_create": candidate_create,
                  "auditor_create": auditor_create, "candidate_invocations": 0, "auditor_invocations": 0,
                  "cleanup_created_unstarted_containers": cleanup, "formal_model_fits": 0,
                  "retries": 0, "shared_containers_touched": False}
        save_record(output, record)
        print(json.dumps(record, indent=2, sort_keys=True))
        raise SystemExit(2)

    candidate = start_capture(candidate_create, output, "candidate")
    host_sha = sha256(package / "preformal" / "host_candidate.json")
    raw_path = candidate_output / "raw.json"
    raw_sha = sha256(raw_path) if raw_path.is_file() else None
    audit = None
    if candidate["exit_code"] == 0 and raw_path.is_file():
        audit = start_capture(auditor_create, output, "auditor")
    audit_path = audit_output / "AUDIT.json"
    audit_json = json.loads(audit_path.read_text(encoding="utf-8")) if audit_path.is_file() else None
    replicated = raw_sha == host_sha
    if candidate["exit_code"] != 0 or audit is None or audit["exit_code"] != 0 or not audit_json or audit_json.get("errors"):
        status = "STOP_EXECUTION_OR_AUDIT"
    elif not replicated:
        status = "STOP_REPLICATION_DIVERGENCE"
    elif audit_json.get("geometry_decision") == "HOLD_GEOMETRY_NOT_IDENTIFIABLE":
        status = "REPLICATION_PASS_WITH_GEOMETRY_HOLD"
    else:
        status = "PASS_GEOMETRY_FEASIBLE"
    record = {"schema": "spatial-block-6590-t1-geometry-recovery-run-record-v1",
              "allocation": freeze["allocation"], "status": status,
              "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
              "freeze_sha256": sha256(root / "FREEZE.json"),
              "parent_freeze_sha256": sha256(package / "FREEZE.json"),
              "git_head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=package, text=True).strip(),
              "image_id": env["image_id"], "image_manifest_digest": env["image_manifest_digest"],
              "platform": env["platform"], "network": env["network"], "resource_limits": resources,
              "candidate": candidate, "auditor": audit,
              "audit_decision": audit_json.get("decision") if audit_json else None,
              "geometry_decision": audit_json.get("geometry_decision") if audit_json else None,
              "preformal_host_candidate_sha256": host_sha, "container_candidate_sha256": raw_sha,
              "byte_for_byte_reproduction": replicated, "formal_model_fits": 0,
              "candidate_invocations": 1, "auditor_invocations": int(audit is not None),
              "retries": 0, "shared_containers_touched": False}
    save_record(output, record)
    if status != "STOP_EXECUTION_OR_AUDIT":
        for item in (candidate, audit):
            if item:
                invoke(["docker", "rm", item["container_id"]])
    print(json.dumps(record, indent=2, sort_keys=True))
    if status == "STOP_EXECUTION_OR_AUDIT":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
