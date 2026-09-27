from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
RUN = Path(__file__).resolve().parent / "evidence/seed-284921"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    frozen = json.loads((RUN / "frozen-inputs.json").read_text())
    result = json.loads((RUN / "contract-result.json").read_text())
    checks = result["checks"]
    positive = {key: value for key, value in checks.items()
                if key != "formal_task_or_model_call_invoked"}
    source = ROOT / "research/integration/issue_2849_task1_orbstack_contract_v21/probe_v21.py"
    audit = {
        "issue": 2849,
        "seed": 284921,
        "status": "PASS_CONSTRUCTION_SIGNALS_WITH_GATE_CLASSIFICATION_DEFECT"
        if all(positive.values()) and checks["formal_task_or_model_call_invoked"] is False
        else "STOP_CONSTRUCTION",
        "registered_gate_status": result["status"],
        "checks": {
            "all_positive_construction_signals": all(positive.values()),
            "no_task_or_model_call_invariant": checks["formal_task_or_model_call_invoked"] is False,
            "runner_status_aggregation_bug": result["status"] == "STOP_CONSTRUCTION"
            and all(positive.values())
            and checks["formal_task_or_model_call_invoked"] is False,
            "source_hash_matches_preregistration": sha(source) == frozen["probe_sha256"],
            "outer_image_matches_preregistration": result["checks"]["pinned_outer_image_identity"],
            "network_disabled_socket_probe": "--network" in result["socket_probe_command"]
            and result["socket_probe_command"][result["socket_probe_command"].index("--network") + 1] == "none",
            "one_container_and_zero_task_model_calls": result["container_invocations"] == 1
            and result["task_started"] is False
            and result["host_broker_started"] is False
            and result["model_calls"] == 0,
        },
        "scope": "OrbStack socket and selected-backend mount construction only; not a task/model result",
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
    return 0 if audit["status"].startswith("PASS_") and all(audit["checks"].values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
