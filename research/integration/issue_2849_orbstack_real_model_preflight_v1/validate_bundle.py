#!/usr/bin/env python3
"""Check the Issue #2849 retained failure and its local SHA-256 manifest."""
import argparse
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit_semantics() -> None:
    run = ROOT / "evidence/attempts-live-v2/experiment-result.json"
    data = json.loads(run.read_text(encoding="utf-8"))
    assert data["overall_status"] == "STOP_OR_FAIL"
    assert data["formal_six_task_allocation_started"] is False
    assert [item["schema_name"] for item in data["attempts"]] == ["plain"]
    attempt = ROOT / "evidence/attempts-live-v2/plain"
    result = json.loads((attempt / "attempt-result.json").read_text(encoding="utf-8"))
    assert result["status"] == "STOP_TRANSPORT_OR_CALL_FAILED"
    assert result["container_returncode"] == 1
    assert result["broker_returncode"] == 0
    assert result["backend_selected_by_resolver"] is True
    assert result["counts"] == {"requests": 1, "broker_receipts": 1, "responses": 1}
    assert not (attempt / "repo/preflight-result/model-call/process.json").exists()
    request = next((attempt / "ipc").glob("*.request.json"))
    broker = next((attempt / "ipc").glob("*.broker.json"))
    request_data = json.loads(request.read_text(encoding="utf-8"))
    broker_data = json.loads(broker.read_text(encoding="utf-8"))
    assert request_data["authority_granted"] is False
    assert request_data["mode"] == "handle" and request_data["image"] is None
    assert broker_data["host_cli_invoked"] is True
    assert broker_data["returncode"] == 0 and broker_data["authority_granted"] is False
    audit = json.loads((attempt / "independent-audit.json").read_text(encoding="utf-8"))
    assert audit["returncode"] == 0
    observed = json.loads(audit["stdout"].strip().splitlines()[-1])
    assert observed["audit_status"] == "PASS_FAILURE_REPRODUCED"
    assert all(observed["checks"].values())
    assert observed["completed_item_types"] == ["error", "agent_message"]
    assert observed["runner_process_receipt_present"] is False
    assert not (ROOT / "evidence/attempts-live-v2/compiled").exists()
    frozen_runner = attempt / "repo/container_host_model_ipc_runner_v1.py"
    assert sha(frozen_runner) == "091fbe29e2ecfb7eba1d77c124d22c67b3d2487950fd52b5b8307e397dc835b2"
    assert sha(attempt / "repo/instructions.txt") == "fd2785852cd55d2a742fba02f3f214839c912a016e9782339e1eb888d2cfb4ef"
    assert sha(attempt / "repo/schema.json") == "0631ab7b7ba0aaf77a4cbdf758a8dbfba557dfb5120a9d5aa789223c97944291"

    first = ROOT / "evidence/attempts-live-v1/plain"
    assert not list((first / "ipc").glob("*.request.json")) if (first / "ipc").exists() else True
    assert not (first / "attempt-result.json").exists()


def files_for_manifest():
    return sorted(path for path in ROOT.rglob("*")
                  if path.is_file() and path.name != "SHA256SUMS")


def write_manifest() -> None:
    lines = [f"{sha(path)}  {path.relative_to(ROOT).as_posix()}"
             for path in files_for_manifest()]
    (ROOT / "SHA256SUMS").write_text("\n".join(lines) + "\n", encoding="utf-8")


def verify_manifest() -> None:
    manifest = ROOT / "SHA256SUMS"
    expected = {}
    for line in manifest.read_text(encoding="utf-8").splitlines():
        digest, relative = line.split("  ", 1)
        if relative in expected:
            raise ValueError("duplicate manifest path: " + relative)
        expected[relative] = digest
    actual = {path.relative_to(ROOT).as_posix(): sha(path)
              for path in files_for_manifest()}
    if expected != actual:
        missing = sorted(set(expected) - set(actual))
        unlisted = sorted(set(actual) - set(expected))
        mismatched = sorted(path for path in set(expected) & set(actual)
                            if expected[path] != actual[path])
        raise ValueError(json.dumps({"missing": missing, "unlisted": unlisted,
                                     "mismatched": mismatched}, sort_keys=True))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write-manifest", action="store_true")
    args = parser.parse_args()
    audit_semantics()
    if args.write_manifest:
        write_manifest()
    verify_manifest()
    print("PASS_BUNDLE_INTEGRITY_AND_FAILURE_CLASSIFICATION")


if __name__ == "__main__":
    main()
