"""Independent audit of a retained synthetic OrbStack v1 transport run."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def audit(root: Path) -> dict:
    root = root.resolve()
    command = json.loads((root / "container-command.json").read_text())
    image = json.loads((root / "docker-image-inspect.json").read_text())[0]
    exit_codes = json.loads((root / "exit-codes.json").read_text())
    request_files = sorted((root / "ipc").glob("*.request.json"))
    assert len(request_files) == 1, f"expected one IPC request, got {len(request_files)}"
    request = json.loads(request_files[0].read_text())
    request_id = request["request_id"]
    broker = json.loads((root / "ipc" / f"{request_id}.broker.json").read_text())
    process = json.loads((root / "out/runner/process.json").read_text())
    events = [json.loads(line) for line in
              (root / "out/runner/events.jsonl").read_text().splitlines()]
    source = json.loads((root / "source-sha256.json").read_text())
    checks = {
        "orbstack_context": command[command.index("--context") + 1] == "orbstack",
        "network_disabled": command[command.index("--network") + 1] == "none",
        "image_id_pinned": image["Id"] == "sha256:e47cbddc70722a816758a4a1c27cf2a38071c889670be98bf3eacdc9fff17916",
        "container_exit_zero": exit_codes["container"] == 0,
        "broker_exit_zero": exit_codes["broker"] == 0,
        "one_non_authoritative_request": len(request_files) == 1 and request["authority_granted"] is False,
        "request_asset_hashes_match": request["schema_sha256"] == sha(root / "repo/schema.json") and request["instructions_sha256"] == sha(root / "repo/instructions.txt"),
        "broker_identity_matches_fake_cli": broker["host_cli_identity"]["path"] == str((root / "fake-codex").resolve()) and broker["host_cli_identity"]["sha256"] == sha(root / "fake-codex") and broker["host_cli_identity"]["version"] == "codex fake-transport-v1",
        "broker_reported_success": broker["returncode"] == 0 and broker["host_cli_invoked"] is True and broker["authority_granted"] is False,
        "runner_reported_non_authority": process["authority_granted"] is False and process["boundary"] == "container-to-host-model-ipc",
        "synthetic_event_sequence": [event["type"] for event in events] == ["thread.started", "item.completed", "turn.completed"],
        "source_hashes_match": source["broker_sha256"] == sha(root.parents[4] / "runtime/host_model_ipc_broker_v1.py") and source["runner_sha256"] == sha(root.parents[4] / "research/live_control/container_host_model_ipc_runner_v1.py") and source["test_sha256"] == sha(root.parents[4] / "research/live_control/issue_3311_host_ipc_v1/test_orbstack_v1_transport.py"),
        "stderr_empty": not (root / "container.stderr.txt").read_text().strip() and not (root / "broker.stderr.txt").read_text().strip(),
    }
    return {
        "disposition": "PASS_V1_SYNTHETIC_TRANSPORT_ONLY" if all(checks.values()) else "FAIL_AUDIT",
        "scope": "synthetic CLI transport; not a real model call, schema endpoint, GUI, task, or efficiency result",
        "evidence_root": str(root),
        "checks": checks,
    }


def main() -> int:
    if len(sys.argv) != 2:
        print(f"usage: {sys.argv[0]} EVIDENCE_DIR", file=sys.stderr)
        return 2
    report = audit(Path(sys.argv[1]))
    root = Path(sys.argv[1]).resolve()
    manifest = {str(path.relative_to(root)): sha(path) for path in sorted(root.rglob("*"))
                if path.is_file() and path.name not in {"audit.json", "raw-sha256.json"}}
    (root / "raw-sha256.json").write_text(json.dumps(manifest, indent=2) + "\n")
    report["raw_sha256_manifest"] = "raw-sha256.json"
    (root / "audit.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    return 0 if report["disposition"].startswith("PASS_") else 1


if __name__ == "__main__":
    raise SystemExit(main())
