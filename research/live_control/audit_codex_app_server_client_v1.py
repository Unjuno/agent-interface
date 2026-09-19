"""Audit the command-free app-server transport probes."""
import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE / "results/codex-app-server-command-free-probe-v1"


def read(name):
    return json.loads((ROOT / name).read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    failure = read("exact-schema-failure.json")
    success = read("legacy-string-success.json")
    assert failure["status"] == "FAILED_BEFORE_MODEL_TURN"
    assert failure["model_turns_started"] == failure["model_calls"] == 0
    assert failure["error"]["code"] == -32600
    assert sha(ROOT / "exact-schema-attempt.py") == failure["source_sha256"][
        "probe_codex_app_server_client_v1.py"]
    assert success["passed"] is True
    assert success["model_turns_started"] == success["model_calls"] == 0
    assert success["thread_ephemeral"] is True and success["thread_id_present"] is True
    assert success["requested_model_available"] is True
    assert sha(HERE / "probe_codex_app_server_client_v1.py") == success["source_sha256"][
        "probe_codex_app_server_client_v1.py"]
    assert sha(HERE / "codex_app_server_client_v1.py") == success["source_sha256"][
        "codex_app_server_client_v1.py"]
    result = {
        "schema": "codex-app-server-command-free-probe-audit-v1", "passed": True,
        "codex_version": success["codex_version"], "model_calls": 0,
        "exact_generated_shape_rejected": True,
        "legacy_thread_sandbox_string_accepted": True,
        "ephemeral_thread_created": True,
        "scope": "command-free protocol compatibility only; interruption remains untested",
    }
    (ROOT / "audit.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
