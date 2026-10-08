"""Verify artifact, build one image, invoke one candidate, then raw-only audit."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

from verify_artifact import verify_and_unpack


HERE = Path(__file__).resolve().parent
IMAGE_TAG = "map01-attack-start-gate-4223-t6:20261001"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def run(argv: list[str], *, log: Path | None = None, check: bool = True, env=None) -> subprocess.CompletedProcess:
    if log is None:
        result = subprocess.run(argv, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env)
        if check and result.returncode:
            raise subprocess.CalledProcessError(result.returncode, argv, result.stdout)
        return result
    with log.open("w", encoding="utf-8") as stream:
        result = subprocess.run(argv, text=True, stdout=stream, stderr=subprocess.STDOUT, env=env)
    if check and result.returncode:
        raise subprocess.CalledProcessError(result.returncode, argv)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--docker-context", default="default")
    args = parser.parse_args()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    execution = {
        "schema": "obstac-map01-start-gate-execution-v1",
        "allocation": "MAP01-ATTACK-ONSET-STARTGATE-4223-T6-20261001-01",
        "source_commit": args.source_commit,
        "formal_candidate_invocations": 0,
        "independent_auditor_invocations": 0,
        "candidate_retry_budget": 0,
        "auditor_retry_budget": 0,
        "network_candidate_and_auditor": "none",
        "formal_status": "NOT_STARTED",
    }
    (out / "OBSTAC_EXECUTION.json").write_text(json.dumps(execution, indent=2, sort_keys=True) + "\n")
    candidate_rc = None
    auditor_rc = None
    return_code = 1
    try:
        with tempfile.TemporaryDirectory(prefix="map01-t6-") as temp_name:
            temp = Path(temp_name)
            artifact_root = temp / "artifact"
            verified = verify_and_unpack(args.artifact.resolve(), artifact_root)
            shutil.copy2(artifact_root / "ARTIFACT_VERIFICATION.json", out / "ARTIFACT_VERIFICATION.json")
            shutil.copy2(artifact_root / "manifest.json", out / "runtime-manifest.json")
            shutil.copytree(artifact_root / "source", out / "runtime-source", dirs_exist_ok=False)
            context_dir = temp / "docker-context"
            context_dir.mkdir()
            shutil.copy2(HERE / "Dockerfile", context_dir / "Dockerfile")
            shutil.copytree(artifact_root / "wheels", context_dir / "wheels")
            build = ["docker", "--context", args.docker_context, "build", "--platform", "linux/amd64",
                     "--tag", IMAGE_TAG, str(context_dir)]
            execution.update({"image_build_argv": build, "image_tag": IMAGE_TAG,
                              "runtime_artifact": verified, "formal_status": "IMAGE_BUILDING"})
            (out / "OBSTAC_EXECUTION.json").write_text(json.dumps(execution, indent=2, sort_keys=True) + "\n")
            built = run(build, log=out / "docker-build.log", check=False)
            if built.returncode:
                raise RuntimeError(f"image build failed with exit {built.returncode}")
            build_rc = subprocess.run(["docker", "--context", args.docker_context, "image", "inspect", IMAGE_TAG,
                                       "--format", "{{.Id}} {{.Os}}/{{.Architecture}}"],
                                      text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            (out / "docker-image-inspect.txt").write_text(build_rc.stdout, encoding="utf-8")
            if build_rc.returncode:
                raise RuntimeError(f"image build/inspect failed: {build_rc.stdout.strip()}")
            image_id, platform = build_rc.stdout.strip().split()
            if platform != "linux/amd64":
                raise RuntimeError(f"wrong image platform: {platform}")
            freeze_bytes = (HERE / "FREEZE.json").read_bytes()
            environment = {
                "OBSTAC_SOURCE_COMMIT": args.source_commit,
                "OBSTAC_IMAGE_ID": image_id,
                "OBSTAC_FREEZE_SHA256": sha(freeze_bytes),
                "OBSTAC_CONSTRUCTION": "0",
                "OBSTAC_PLATFORM": "linux/amd64",
                "OBSTAC_DOCKER_CONTEXT": args.docker_context,
                "OBSTAC_RUNTIME_SOURCE_BASE": "9e6d5ecdbb5440fd5df1883161f2c63b2c3bb245",
                "MAP01_RUNTIME_ARTIFACT_ID": "10398313098",
                "MAP01_RUNTIME_ARTIFACT_SHA256": "522763418610ea10e57e55615fa71e76445200b9f86d208820ea97c77c234f0b",
                "MAP01_SOURCE_ROOT": "/src",
                "MAP01_PROBE_ROOT": "/probe",
            }
            command = ["docker", "--context", args.docker_context, "run", "--rm", "--cidfile",
                       str(out / "candidate.cid"), "--pull=never",
                       "--platform", "linux/amd64", "--network", "none", "--read-only",
                       "--tmpfs", "/tmp:rw,noexec,nosuid,size=2g", "--pids-limit", "128",
                       "--memory", "4g", "--cpus", "2", "--cap-drop", "ALL",
                       "--security-opt", "no-new-privileges", "--workdir", "/tmp",
                       "--mount", f"type=bind,src={out / 'runtime-source'},dst=/src,readonly",
                       "--mount", f"type=bind,src={HERE},dst=/probe,readonly",
                       "--mount", f"type=bind,src={out / 'candidate'},dst=/out"]
            (out / "candidate").mkdir()
            for key, value in environment.items():
                command.extend(["--env", f"{key}={value}"])
            command.extend([IMAGE_TAG, "python", "/probe/start_gate.py", "--source", "/src",
                            "--probe", "/probe", "--out", "/out"])
            execution.update({"image_id": image_id, "image_platform": platform,
                              "obstac_environment": environment, "candidate_argv": command,
                              "formal_candidate_invocations": 1, "formal_status": "CANDIDATE_ARMED"})
            (out / "OBSTAC_EXECUTION.json").write_text(json.dumps(execution, indent=2, sort_keys=True) + "\n")
            candidate = run(command, log=out / "candidate-container.log", check=False)
            candidate_rc = candidate.returncode
            execution["candidate_exit_code"] = candidate_rc
            candidate_cid = out / "candidate.cid"
            execution["candidate_container_id"] = candidate_cid.read_text().strip() if candidate_cid.is_file() else None
            if candidate_rc != 0:
                execution["formal_status"] = "STOP_CANDIDATE"
                raise RuntimeError(f"candidate exited {candidate_rc}; auditor not invoked")

            raw = out / "candidate" / "RAW.json"
            image = out / "candidate" / "initial-observation.png"
            if not raw.is_file() or not image.is_file():
                execution["formal_status"] = "STOP_MISSING_RAW"
                raise RuntimeError("candidate exited zero but required raw/image is absent")
            audit_out = out / "audit"
            audit_out.mkdir()
            auditor = ["docker", "--context", args.docker_context, "run", "--rm", "--cidfile",
                       str(out / "auditor.cid"), "--pull=never",
                       "--platform", "linux/amd64", "--network", "none", "--read-only",
                       "--tmpfs", "/tmp:rw,noexec,nosuid,size=256m", "--pids-limit", "32",
                       "--memory", "1g", "--cpus", "1", "--cap-drop", "ALL",
                       "--security-opt", "no-new-privileges", "--workdir", "/tmp",
                       "--mount", f"type=bind,src={raw},dst=/evidence/RAW.json,readonly",
                       "--mount", f"type=bind,src={out / 'runtime-manifest.json'},dst=/evidence/manifest.json,readonly",
                       "--mount", f"type=bind,src={HERE / 'FREEZE.json'},dst=/evidence/FREEZE.json,readonly",
                       "--mount", f"type=bind,src={image},dst=/evidence/initial-observation.png,readonly",
                       "--mount", f"type=bind,src={out / 'candidate' / 'child.stdout.jsonl'},dst=/evidence/child.stdout.jsonl,readonly",
                       "--mount", f"type=bind,src={out / 'candidate' / 'child.stderr.txt'},dst=/evidence/child.stderr.txt,readonly",
                       "--mount", f"type=bind,src={out / 'OBSTAC_EXECUTION.json'},dst=/evidence/OBSTAC_EXECUTION.json,readonly",
                       "--mount", f"type=bind,src={HERE / 'audit_start_gate.py'},dst=/audit.py,readonly",
                       "--mount", f"type=bind,src={audit_out},dst=/out",
                       *[item for pair in environment.items() for item in ("--env", f"{pair[0]}={pair[1]}")],
                       IMAGE_TAG, "python", "/audit.py", "--raw", "/evidence/RAW.json",
                       "--manifest", "/evidence/manifest.json", "--image", "/evidence/initial-observation.png",
                       "--freeze", "/evidence/FREEZE.json", "--stdout", "/evidence/child.stdout.jsonl",
                       "--stderr", "/evidence/child.stderr.txt", "--execution", "/evidence/OBSTAC_EXECUTION.json",
                       "--out", "/out/AUDIT.json"]
            execution.update({"auditor_argv": auditor, "independent_auditor_invocations": 1,
                              "formal_status": "AUDITOR_ARMED"})
            (out / "OBSTAC_EXECUTION.json").write_text(json.dumps(execution, indent=2, sort_keys=True) + "\n")
            audited = run(auditor, log=out / "auditor-container.log", check=False)
            auditor_rc = audited.returncode
            execution["auditor_exit_code"] = auditor_rc
            auditor_cid = out / "auditor.cid"
            execution["auditor_container_id"] = auditor_cid.read_text().strip() if auditor_cid.is_file() else None
            execution["formal_status"] = "PASS_START_GATE_ONLY" if auditor_rc == 0 else "STOP_AUDIT"
            return_code = auditor_rc
    except Exception as exc:
        execution["formal_status"] = execution.get("formal_status", "STOP_SETUP")
        if execution["formal_status"] not in ("STOP_CANDIDATE", "STOP_MISSING_RAW", "STOP_AUDIT"):
            execution["formal_status"] = "STOP_SETUP"
        execution["failure"] = f"{type(exc).__name__}: {exc}"
        return_code = 1
    finally:
        execution["candidate_exit_code"] = candidate_rc
        execution["auditor_exit_code"] = auditor_rc
        (out / "OBSTAC_EXECUTION.json").write_text(json.dumps(execution, indent=2, sort_keys=True) + "\n")
    return return_code


if __name__ == "__main__":
    raise SystemExit(main())
