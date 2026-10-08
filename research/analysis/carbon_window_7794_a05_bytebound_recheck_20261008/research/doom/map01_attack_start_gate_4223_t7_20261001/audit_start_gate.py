"""Independent raw-only audit; does not import or execute the candidate."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import time


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def audit(raw_path: Path, artifact_manifest_path: Path, image_path: Path, freeze_path: Path,
          stdout_path: Path, stderr_path: Path, execution_path: Path, out_path: Path) -> dict:
    raw = json.loads(raw_path.read_text(encoding="utf-8"))
    manifest = json.loads(artifact_manifest_path.read_text(encoding="utf-8"))
    freeze_bytes = freeze_path.read_bytes()
    freeze = json.loads(freeze_bytes)
    execution = json.loads(execution_path.read_text(encoding="utf-8"))
    checks: dict[str, bool] = {}
    errors: list[str] = []

    def check(name: str, condition: bool) -> None:
        checks[name] = bool(condition)
        if not condition:
            errors.append(name)

    check("schema", raw.get("schema") == "map01-attack-start-gate-raw-v1")
    check("allocation", raw.get("allocation") == "MAP01-ATTACK-ONSET-STARTGATE-4223-T7-20261001-01")
    check("decision", raw.get("decision") == "PASS_START_GATE_ONLY" and raw.get("failure") is None)
    check("single_candidate_no_retry", raw.get("candidate_invocations") == 1 and raw.get("retry_count") == 0)
    check("linux_amd64", raw.get("architecture") == "x86_64")
    check("versions", raw.get("python", "").startswith("3.13.5") and raw.get("vizdoom") == "1.3.0")
    env = raw.get("environment", {})
    check("obstac_receipt", all(env.get(k) for k in (
        "OBSTAC_SOURCE_COMMIT", "OBSTAC_IMAGE_ID", "OBSTAC_FREEZE_SHA256", "OBSTAC_PLATFORM", "OBSTAC_DOCKER_CONTEXT"))
        and env.get("OBSTAC_CONSTRUCTION") == "0")
    expected_env = {
        "OBSTAC_SOURCE_COMMIT": os.environ.get("OBSTAC_SOURCE_COMMIT"),
        "OBSTAC_IMAGE_ID": os.environ.get("OBSTAC_IMAGE_ID"),
        "OBSTAC_FREEZE_SHA256": os.environ.get("OBSTAC_FREEZE_SHA256"),
        "OBSTAC_CONSTRUCTION": "0",
        "OBSTAC_PLATFORM": "linux/amd64",
        "OBSTAC_DOCKER_CONTEXT": os.environ.get("OBSTAC_DOCKER_CONTEXT"),
        "OBSTAC_RUNTIME_SOURCE_BASE": freeze.get("runtime_source_base"),
    }
    check("obstac_environment_matches_invocation", all(env.get(k) == v for k, v in expected_env.items()))
    check("freeze_hash", env.get("OBSTAC_FREEZE_SHA256") == sha(freeze_bytes))
    check("freeze_allocation", freeze.get("allocation") == raw.get("allocation"))
    check("runtime_artifact_identity", raw.get("runtime_artifact_id") == freeze.get("runtime_artifact_id")
          and raw.get("runtime_artifact_sha256") == freeze.get("runtime_artifact_sha256"))
    check("runtime_source_base", raw.get("runtime_source_base") == env.get("OBSTAC_RUNTIME_SOURCE_BASE")
          == freeze.get("runtime_source_base"))
    candidate_argv = execution.get("candidate_argv", [])
    check("execution_receipt", execution.get("schema") == "obstac-map01-start-gate-execution-v1"
          and execution.get("allocation") == raw.get("allocation")
          and execution.get("source_commit") == env.get("OBSTAC_SOURCE_COMMIT")
          and execution.get("image_id") == env.get("OBSTAC_IMAGE_ID")
          and execution.get("candidate_exit_code") == 0
          and execution.get("formal_candidate_invocations") == 1
          and execution.get("independent_auditor_invocations") == 1
          and execution.get("candidate_retry_budget") == 0
          and execution.get("formal_status") == "AUDITOR_ARMED")
    build_artifact = execution.get("runtime_artifact", {})
    check("execution_artifact_identity", build_artifact.get("artifact_id") == freeze.get("runtime_artifact_id")
          and build_artifact.get("artifact_sha256") == freeze.get("runtime_artifact_sha256")
          and execution.get("image_platform") == "linux/amd64")
    check("candidate_container_constraints", "--network" in candidate_argv
          and candidate_argv[candidate_argv.index("--network") + 1] == "none"
          and "--read-only" in candidate_argv
          and "--platform" in candidate_argv
          and candidate_argv[candidate_argv.index("--platform") + 1] == "linux/amd64"
          and any("dst=/src,readonly" in item for item in candidate_argv))
    auditor_argv = execution.get("auditor_argv", [])
    check("auditor_container_constraints", "--network" in auditor_argv
          and auditor_argv[auditor_argv.index("--network") + 1] == "none"
          and "--read-only" in auditor_argv
          and "--platform" in auditor_argv
          and auditor_argv[auditor_argv.index("--platform") + 1] == "linux/amd64")
    candidate_probe_argv = execution.get("candidate_mount_probe_argv", [])
    candidate_probe = execution.get("candidate_mount_probe_output")
    check("candidate_output_mount_probe", execution.get("candidate_mount_probe_invocations") == 1
          and execution.get("candidate_mount_probe_exit_code") == 0
          and execution.get("candidate_output_host_mode") == "0o777"
          and isinstance(candidate_probe, dict) and candidate_probe.get("mode") == "0o777"
          and "--cap-drop" in candidate_probe_argv
          and candidate_probe_argv[candidate_probe_argv.index("--cap-drop") + 1] == "ALL"
          and "--network" in candidate_probe_argv
          and candidate_probe_argv[candidate_probe_argv.index("--network") + 1] == "none")
    auditor_probe_argv = execution.get("auditor_mount_probe_argv", [])
    auditor_probe = execution.get("auditor_mount_probe_output")
    check("auditor_output_mount_probe", execution.get("auditor_mount_probe_invocations") == 1
          and execution.get("auditor_mount_probe_exit_code") == 0
          and execution.get("auditor_output_host_mode") == "0o777"
          and isinstance(auditor_probe, dict) and auditor_probe.get("mode") == "0o777"
          and "--cap-drop" in auditor_probe_argv
          and auditor_probe_argv[auditor_probe_argv.index("--cap-drop") + 1] == "ALL"
          and "--network" in auditor_probe_argv
          and auditor_probe_argv[auditor_probe_argv.index("--network") + 1] == "none")

    events = raw.get("events")
    check("events_array", isinstance(events, list))
    events = events if isinstance(events, list) else []
    names = [e.get("event") for e in events if isinstance(e, dict)]
    check("one_ready", names.count("ready") == 1)
    ready_index = names.index("ready") if "ready" in names else -1
    observations = [e for e in events if isinstance(e, dict) and e.get("event") == "observation"]
    check("one_initial_observation", len(observations) >= 1 and observations[0].get("id") == "initial")
    initial = observations[0] if observations else {}
    initial_index = next((i for i, e in enumerate(events) if isinstance(e, dict) and e.get("event") == "observation"), -1)
    check("ready_precedes_initial", ready_index >= 0 and initial_index > ready_index)
    check("exact_first_sequence", initial.get("sequence") == 1 and initial.get("exact") is True)
    image_exists = image_path.is_file() and image_path.stat().st_size > 0
    check("image_retained", image_exists)
    if image_exists:
        from PIL import Image
        with Image.open(image_path) as image:
            image_rgb_hash = hashlib.sha256(image.convert("RGB").tobytes()).hexdigest()
    else:
        image_rgb_hash = None
    check("rgb_image_matches", image_rgb_hash == initial.get("frame_rgb_sha256"))
    check("png_hash_matches_raw", image_exists and raw.get("initial_observation_png_sha256") == sha(image_path.read_bytes()))

    commands = raw.get("sent_commands")
    check("finish_only", commands == [{"op": "finish"}])
    command_events = [e for e in events if isinstance(e, dict) and e.get("event") == "command"]
    check("one_finish_command_recorded", len(command_events) == 1 and command_events[0].get("command") == {"op": "finish"})
    check("no_input_authority", raw.get("input_admission_count") == 0
          and not any(isinstance(e, dict) and e.get("event") == "input_admission" for e in events))
    check("one_post_score", raw.get("post_control_score_count") == 1 and names.count("post_control_score") == 1)
    check("child_exit_zero", raw.get("child_returncode") == 0)
    stdout_bytes = stdout_path.read_bytes() if stdout_path.is_file() else b""
    stderr_bytes = stderr_path.read_bytes() if stderr_path.is_file() else b""
    check("child_logs_hashed", raw.get("child_stdout_sha256") == sha(stdout_bytes)
          and raw.get("child_stderr_sha256") == sha(stderr_bytes))
    stdout_events = []
    stdout_is_json_objects = True
    try:
        for line in stdout_bytes.decode("utf-8").splitlines():
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue  # preserve but allow non-JSON engine diagnostics on stdout
            if not isinstance(event, dict):
                stdout_is_json_objects = False
                break
            stdout_events.append(event)
    except UnicodeDecodeError:
        stdout_is_json_objects = False
    check("stdout_events_match_raw", stdout_is_json_objects and stdout_events == events)
    check("source_manifest_base", manifest.get("base_commit") == "9e6d5ecdbb5440fd5df1883161f2c63b2c3bb245")
    runtime_sources = raw.get("runtime_sources", {})
    check("runtime_source_map_present", isinstance(runtime_sources, dict) and len(runtime_sources) >= 15)
    source_files = manifest.get("files", {})
    source_matches = bool(runtime_sources) and all(
        source_files.get("research/" + path, {}).get("sha256") == digest
        for path, digest in runtime_sources.items()
    )
    check("runtime_source_hashes", source_matches)
    reconstructed_sources = (json.dumps(runtime_sources, indent=2, sort_keys=True) + "\n").encode("utf-8")
    check("runtime_source_map_digest", raw.get("runtime_sources_sha256") == sha(reconstructed_sources))

    report = {
        "schema": "map01-attack-start-gate-audit-v1",
        "allocation": raw.get("allocation"),
        "decision": "PASS_START_GATE_ONLY" if not errors else "STOP_AUDIT",
        "checks": checks,
        "errors": errors,
        "independent_of_candidate": True,
        "scope": "actual ViZDoom initialization, ready, first exact observation and neutral finish only",
        "raw_sha256": sha(raw_path.read_bytes()),
        "initial_png_sha256": sha(image_path.read_bytes()) if image_exists else None,
        "initial_rgb_sha256_recomputed": image_rgb_hash,
        "audited_at_unix_ns": time.time_ns(),
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--image", type=Path, required=True)
    parser.add_argument("--freeze", type=Path, required=True)
    parser.add_argument("--stdout", type=Path, required=True)
    parser.add_argument("--stderr", type=Path, required=True)
    parser.add_argument("--execution", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    report = audit(args.raw, args.manifest, args.image, args.freeze, args.stdout,
                   args.stderr, args.execution, args.out)
    print(json.dumps({"decision": report["decision"], "errors": report["errors"]}, sort_keys=True))
    return 0 if report["decision"] == "PASS_START_GATE_ONLY" else 1


if __name__ == "__main__":
    raise SystemExit(main())
