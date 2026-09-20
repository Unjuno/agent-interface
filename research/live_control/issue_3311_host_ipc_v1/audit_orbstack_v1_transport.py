"""Independent audit of a retained synthetic OrbStack v1 transport run."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_source_sha(revision: str, repository_path: str) -> str:
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise ValueError("source revision must be a full lowercase commit SHA")
    repo = Path(__file__).resolve().parents[3]
    completed = subprocess.run(["git", "show", f"{revision}:{repository_path}"],
                               cwd=repo, capture_output=True, check=True)
    return hashlib.sha256(completed.stdout).hexdigest()


def docker_run_image_reference(command: list[str]) -> str | None:
    """Return the image reference consumed by the docker run command."""
    value_options = {
        "-e", "--env", "-v", "--volume", "--network", "--entrypoint",
        "-w", "--workdir", "--name", "--user", "--platform", "--mount",
        "-p", "--publish", "--cpus", "--memory",
    }
    try:
        index = command.index("run") + 1
    except ValueError:
        return None
    while index < len(command):
        token = command[index]
        if token == "--":
            return command[index + 1] if index + 1 < len(command) else None
        if token in value_options:
            index += 2
            continue
        if token.startswith("-"):
            index += 1
            continue
        return token
    return None


def verify_raw_manifest(root: Path) -> bool:
    """Compare retained raw files with the frozen manifest without writing."""
    root = root.resolve()
    manifest_path = root / "raw-sha256.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        actual = {
            path.relative_to(root).as_posix(): sha(path)
            for path in sorted(root.rglob("*"))
            if path.is_file() and path not in {manifest_path, root / "audit.json"}
        }
    except (OSError, json.JSONDecodeError):
        return False
    return manifest == actual


def audit(root: Path) -> dict:
    root = root.resolve()
    manifest_matches = verify_raw_manifest(root)
    command = json.loads((root / "container-command.json").read_text())
    image = json.loads((root / "docker-image-inspect.json").read_text())[0]
    exit_codes = json.loads((root / "exit-codes.json").read_text())
    request_files = sorted((root / "ipc").glob("*.request.json"))
    assert len(request_files) == 1, f"expected one IPC request, got {len(request_files)}"
    request = json.loads(request_files[0].read_text())
    request_id = request["request_id"]
    broker = json.loads((root / "ipc" / f"{request_id}.broker.json").read_text())
    response = [json.loads(line) for line in
                (root / "ipc" / f"{request_id}.response.jsonl").read_text().splitlines()]
    process = json.loads((root / "out/runner/process.json").read_text())
    events = [json.loads(line) for line in
              (root / "out/runner/events.jsonl").read_text().splitlines()]
    source = json.loads((root / "source-sha256.json").read_text())
    revisions_path = root.parents[1] / "source-revisions.json"
    revision = json.loads(revisions_path.read_text())[root.name]
    cli_path = broker["host_cli_identity"]["path"].replace("\\", "/")
    run_image = docker_run_image_reference(command)
    inspected_refs = set(image.get("RepoTags") or []) | set(image.get("RepoDigests") or []) | {image.get("Id")}
    checks = {
        "orbstack_context": command[command.index("--context") + 1] == "orbstack",
        "network_disabled": command[command.index("--network") + 1] == "none",
        "image_id_pinned": image["Id"] == "sha256:e47cbddc70722a816758a4a1c27cf2a38071c889670be98bf3eacdc9fff17916",
        "run_image_matches_inspect": run_image in inspected_refs,
        "container_exit_zero": exit_codes["container"] == 0,
        "broker_exit_zero": exit_codes["broker"] == 0,
        "one_non_authoritative_request": len(request_files) == 1 and request["authority_granted"] is False,
        "request_asset_hashes_match": request["schema_sha256"] == sha(root / "repo/schema.json") and request["instructions_sha256"] == sha(root / "repo/instructions.txt"),
        "broker_identity_matches_fake_cli": Path(cli_path).name == "fake-codex" and broker["host_cli_identity"]["sha256"] == sha(root / "fake-codex") and broker["host_cli_identity"]["version"] == "codex fake-transport-v1",
        "broker_reported_success": broker["returncode"] == 0 and broker["host_cli_invoked"] is True and broker["authority_granted"] is False,
        "runner_reported_non_authority": process["authority_granted"] is False and process["boundary"] == "container-to-host-model-ipc",
        "broker_response_matches_runner_events": response == events,
        "synthetic_event_sequence": [event["type"] for event in events] == ["thread.started", "item.completed", "turn.completed"],
        "source_hashes_match": source["broker_sha256"] == git_source_sha(revision, "runtime/host_model_ipc_broker_v1.py") and source["runner_sha256"] == git_source_sha(revision, "research/live_control/container_host_model_ipc_runner_v1.py") and source["test_sha256"] == git_source_sha(revision, "research/live_control/issue_3311_host_ipc_v1/test_orbstack_v1_transport.py"),
        "stderr_empty": not (root / "container.stderr.txt").read_text().strip() and not (root / "broker.stderr.txt").read_text().strip(),
        "raw_manifest_matches": manifest_matches,
    }
    return {
        "disposition": "PASS_V1_SYNTHETIC_TRANSPORT_ONLY" if all(checks.values()) else "FAIL_AUDIT",
        "scope": "synthetic CLI transport; not a real model call, schema endpoint, GUI, task, or efficiency result",
        "evidence_root": str(root),
        "checks": checks,
    }


def main() -> int:
    if len(sys.argv) not in (2, 4) or (len(sys.argv) == 4 and sys.argv[2] != "--output"):
        print(f"usage: {sys.argv[0]} EVIDENCE_DIR [--output REPORT.json]", file=sys.stderr)
        return 2
    evidence_root = Path(sys.argv[1]).resolve()
    report = audit(evidence_root)
    rendered = json.dumps(report, indent=2) + "\n"
    if len(sys.argv) >= 4:
        output_path = Path(sys.argv[3]).resolve()
        try:
            output_path.relative_to(evidence_root)
        except ValueError:
            pass
        else:
            print("audit output must be outside the immutable evidence root", file=sys.stderr)
            return 2
        manifest = evidence_root / "raw-sha256.json"
        if output_path == manifest or output_path in evidence_root.rglob("*"):
            print("audit output must not overwrite retained evidence", file=sys.stderr)
            return 2
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if report["disposition"].startswith("PASS_") else 1


if __name__ == "__main__":
    raise SystemExit(main())
