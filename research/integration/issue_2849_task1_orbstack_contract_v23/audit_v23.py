from __future__ import annotations

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUN = HERE / "evidence/seed-284923"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    frozen = json.loads((RUN / "frozen-inputs.json").read_text())
    result = json.loads((RUN / "probe-result.json").read_text())
    fixture = RUN / "fixture/payload.txt"
    source = HERE / "probe_v23.py"
    checks = {
        "probe_and_fixture_match_preregistration": sha(source) == frozen["probe_sha256"]
        and sha(fixture) == frozen["fixture_sha256"],
        "pinned_images_match_preregistration": result["checks"]["pinned_outer_and_nested_images"]
        and frozen["outer_image"].endswith(" arm64") and frozen["nested_image"].endswith(" arm64"),
        "nested_read_only_bind_digest_exact": result["checks"]["nested_container_read_only_fixture_digest_exact"]
        and result["observed_fixture_sha256"] == frozen["fixture_sha256"],
        "both_networks_disabled": result["checks"]["outer_and_nested_commands_network_disabled"],
        "outer_and_nested_exit_zero": result["outer_returncode"] == 0
        and result["nested_receipt"]["returncode"] == 0,
        "no_task_or_model_activity": result["task_started"] is False
        and result["host_broker_started"] is False and result["model_calls"] == 0,
        "registered_runner_status_pass": result["status"] == "PASS_NESTED_BIND",
    }
    audit = {
        "issue": 2849, "seed": 284923,
        "status": "PASS_NESTED_BIND" if all(checks.values()) else "STOP_NESTED_BIND",
        "checks": checks,
        "scope": "OrbStack nested bind-mount transport only; no task/model result",
        "expected_fixture_sha256": frozen["fixture_sha256"],
        "observed_fixture_sha256": result["observed_fixture_sha256"],
        "evidence_sha256": {"frozen_inputs": sha(RUN / "frozen-inputs.json"),
                             "probe_result": sha(RUN / "probe-result.json"),
                             "probe_source": sha(source)},
        "authority_granted": False,
    }
    (RUN / "independent-audit.json").write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n")
    files = sorted(path for path in RUN.rglob("*") if path.is_file() and path.name != "SHA256SUMS")
    (RUN / "SHA256SUMS").write_text("".join(
        f"{sha(path)}  {path.relative_to(RUN)}\n" for path in files))
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
