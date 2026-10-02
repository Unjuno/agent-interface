from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path


SOURCE_FILES = ("README.md", "PROTOCOL.md", "Dockerfile", "candidate.py", "auditor.py",
                "test_geometry.py", "run_formal.py", "preformal/README.md",
                "../../../.github/workflows/analysis-index.yml")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(command):
    return subprocess.run(command, text=True, capture_output=True, check=False)


def verify(root: Path, freeze: dict):
    if set(freeze.get("source_sha256", {})) != set(SOURCE_FILES):
        raise ValueError("frozen source inventory mismatch")
    image_result = run(["docker", "image", "inspect", freeze["image"]])
    if image_result.returncode:
        raise ValueError(f"pinned image unavailable: {image_result.stderr.strip()}")
    image_info = json.loads(image_result.stdout)[0]
    if (image_info.get("Id") != freeze.get("image_id") or image_info.get("Os") != "linux"
            or image_info.get("Architecture") != "arm64"
            or freeze.get("image_manifest_digest") not in image_info.get("RepoDigests", [])):
        raise ValueError("pinned local image identity/platform mismatch")
    for name, expected in freeze["source_sha256"].items():
        if sha256(root / name) != expected:
            raise ValueError(f"frozen source hash mismatch: {name}")
    sidecar = root / "FREEZE.sha256"
    expected_freeze_sha = sidecar.read_text(encoding="ascii").split()[0]
    if sha256(root / "FREEZE.json") != expected_freeze_sha:
        raise ValueError("freeze sidecar mismatch")
    baseline = root / "preformal" / "host_candidate.json"
    if sha256(baseline) != freeze.get("preformal_candidate_sha256"):
        raise ValueError("retained preformal host output hash mismatch")


def create_container(name, image, command, mounts):
    args = ["docker", "create", "--name", name, "--platform", "linux/arm64",
            "--network", "none", "--cpus", "1", "--memory", "256m", "--pids-limit", "32",
            "--read-only", "--cap-drop", "ALL", "--security-opt", "no-new-privileges"]
    for mount in mounts:
        args.extend(["--mount", mount])
    args.extend([image, *command])
    result = run(args)
    if result.returncode:
        raise RuntimeError(f"docker create failed: {result.stderr.strip()}")
    return result.stdout.strip()


def start_capture(container_id: str, out: Path, stem: str):
    result = run(["docker", "start", "--attach", container_id])
    (out / f"{stem}.stdout.txt").write_text(result.stdout, encoding="utf-8")
    (out / f"{stem}.stderr.txt").write_text(result.stderr, encoding="utf-8")
    inspect = run(["docker", "inspect", container_id])
    if inspect.returncode:
        raise RuntimeError(f"docker inspect failed for {container_id}: {inspect.stderr.strip()}")
    metadata = json.loads(inspect.stdout)[0]
    return {"container_id": container_id, "exit_code": result.returncode,
            "started_at": metadata["State"].get("StartedAt"), "finished_at": metadata["State"].get("FinishedAt"),
            "state": metadata["State"], "host_config": metadata["HostConfig"],
            "stdout_sha256": sha256(out / f"{stem}.stdout.txt"),
            "stderr_sha256": sha256(out / f"{stem}.stderr.txt")}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    freeze = json.loads((root / "FREEZE.json").read_text(encoding="utf-8"))
    verify(root, freeze)
    result_root = root / "results"
    if result_root.exists() and any(result_root.iterdir()):
        raise FileExistsError("formal result path is nonempty; one-shot allocation forbids retry")
    candidate_out = result_root / "candidate"
    audit_out = result_root / "audit"
    candidate_out.mkdir(parents=True)
    audit_out.mkdir(parents=True)
    image = freeze["image"]
    candidate_name = freeze["candidate_container_name"]
    auditor_name = freeze["auditor_container_name"]
    created = datetime.now(timezone.utc).isoformat()
    candidate_id = create_container(candidate_name, image,
        ["python", "/work/candidate.py", "--out", "/out/raw.json"],
        [f"type=bind,src={root},dst=/work,readonly", f"type=bind,src={candidate_out},dst=/out"])
    candidate = start_capture(candidate_id, result_root, "candidate")
    host_baseline_sha = sha256(root / "preformal" / "host_candidate.json")
    candidate_raw_sha = sha256(candidate_out / "raw.json") if (candidate_out / "raw.json").is_file() else None
    byte_reproduction = candidate_raw_sha == host_baseline_sha
    audit = None
    if candidate["exit_code"] == 0 and (candidate_out / "raw.json").is_file():
        auditor_id = create_container(auditor_name, image,
            ["python", "/work/auditor.py", "--raw", "/raw/raw.json", "--out", "/out/AUDIT.json"],
            [f"type=bind,src={root},dst=/work,readonly",
             f"type=bind,src={candidate_out},dst=/raw,readonly", f"type=bind,src={audit_out},dst=/out"])
        audit = start_capture(auditor_id, result_root, "auditor")
    artifact_hashes = {str(path.relative_to(result_root)): sha256(path)
                       for path in sorted(result_root.rglob("*")) if path.is_file()}
    audit_json = json.loads((audit_out / "AUDIT.json").read_text(encoding="utf-8")) if audit and (audit_out / "AUDIT.json").is_file() else None
    if candidate["exit_code"] != 0 or audit is None or audit["exit_code"] != 0 or not audit_json or audit_json.get("decision") != "PASS_GEOMETRY_AUDIT":
        status = "STOP_EXECUTION_OR_AUDIT"
    elif not byte_reproduction:
        status = "STOP_REPLICATION_DIVERGENCE"
    elif audit_json.get("geometry_decision") == "HOLD_GEOMETRY_NOT_IDENTIFIABLE":
        status = "REPLICATION_PASS_WITH_GEOMETRY_HOLD"
    else:
        status = "PASS_GEOMETRY_FEASIBLE"
    record = {"schema": "spatial-block-6590-t1-geometry-run-record-v1",
              "allocation": freeze["allocation"], "status": status, "created_at": created,
              "freeze_sha256": sha256(root / "FREEZE.json"), "git_head": subprocess.check_output(
                  ["git", "rev-parse", "HEAD"], cwd=root, text=True).strip(),
              "image_id": freeze["image_id"], "image_manifest_digest": freeze["image_manifest_digest"],
              "platform": "linux/arm64", "network": "none", "resource_limits": freeze["resource_limits"],
              "candidate": candidate, "auditor": audit,
              "preformal_host_candidate_sha256": host_baseline_sha,
              "container_candidate_sha256": candidate_raw_sha,
              "byte_for_byte_reproduction": byte_reproduction,
              "audit_decision": audit_json.get("decision") if audit_json else None,
              "geometry_decision": audit_json.get("geometry_decision") if audit_json else None,
              "artifact_sha256": artifact_hashes,
              "formal_candidate_model_fits": 0, "formal_auditor_model_fits": 0,
              "retries": 0, "shared_containers_touched": False}
    (result_root / "RUN_RECORD.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if status != "STOP_EXECUTION_OR_AUDIT":
        for info in (candidate, audit):
            if info:
                run(["docker", "rm", info["container_id"]])
    print(json.dumps(record, indent=2, sort_keys=True))
    if status == "STOP_EXECUTION_OR_AUDIT":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
