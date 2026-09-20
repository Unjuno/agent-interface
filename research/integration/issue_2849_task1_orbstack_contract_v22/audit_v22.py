from __future__ import annotations

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUN = HERE / "evidence/seed-284922"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    frozen = json.loads((RUN / "frozen-inputs.json").read_text())
    result = json.loads((RUN / "contract-result.json").read_text())
    positive = {key: value for key, value in result["checks"].items()
                if key != "no_task_broker_or_model_call_invoked"}
    source = HERE / "probe_v22.py"
    checks = {
        "registered_probe_hash_matches": sha(source) == frozen["probe_sha256"],
        "main_and_dependency_hashes_match_prereg": frozen["main_commit"] == "4b2e84b79633281138b6f72c70e98d5fe9a5bf95"
        and frozen["backend_sha256"] == "f0b49a31500a167df8657fe57fa2565fcd3fa49bc5155db59ae9d8d5785647b2"
        and frozen["broker_sha256"] == "0f6a812effe4807bf2997fba62bbabe8ea26288fcb644d7951b7c5cb24f4be57",
        "all_positive_construction_checks": all(positive.values()),
        "no_task_broker_or_model_calls": result["checks"]["no_task_broker_or_model_call_invoked"] is True
        and result["task_started"] is False and result["host_broker_started"] is False
        and result["model_calls"] == 0,
        "outer_socket_query_success": result["socket_probe"]["returncode"] == 0
        and result["socket_probe"]["stdout"] == "29.4.0 linux/arm64\n",
        "single_network_disabled_container": result["container_invocations"] == 1
        and result["socket_probe_command"][result["socket_probe_command"].index("--network") + 1] == "none",
        "recorded_runner_status_pass": result["status"] == "PASS_CONSTRUCTION",
    }
    audit = {
        "issue": 2849, "seed": 284922,
        "status": "PASS_CONSTRUCTION" if all(checks.values()) else "STOP_CONSTRUCTION",
        "checks": checks,
        "scope": "OrbStack socket reachability and selected-backend mount construction only; no task/model outcome",
        "evidence_sha256": {
            "frozen_inputs": sha(RUN / "frozen-inputs.json"),
            "contract_result": sha(RUN / "contract-result.json"),
            "probe_source": sha(source),
        },
        "authority_granted": False,
    }
    (RUN / "independent-audit.json").write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n")
    files = sorted(path for path in RUN.rglob("*") if path.is_file() and path.name != "SHA256SUMS")
    (RUN / "SHA256SUMS").write_text("".join(
        f"{sha(path)}  {path.relative_to(RUN)}\n" for path in files))
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
