#!/usr/bin/env python3
"""Independent v2 audit; normalizes terminal overstrikes in retained man text."""
import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
F = json.loads((ROOT / "FREEZE.json").read_text())
R = json.loads((ROOT / "RESULT.json").read_text())
OUT = ROOT / "AUDIT.json"


def main():
    if OUT.exists():
        raise SystemExit("STOP_AUDIT_OUTPUT_EXISTS")
    assert subprocess.check_output(["git", "rev-parse", "HEAD"]).decode().strip() == F["base_commit"]
    assert hashlib.sha256((ROOT / "candidate.py").read_bytes()).hexdigest() == F["candidate_sha256"]
    assert hashlib.sha256(Path(__file__).read_bytes()).hexdigest() == F["auditor_v2_sha256"]
    assert hashlib.sha256(Path(F["powermetrics_path"]).read_bytes()).hexdigest() == F["powermetrics_sha256"]
    assert R["base_commit"] == F["base_commit"]
    assert R["privilege_escalation_attempted"] is False and R["gui_model_route_or_task_runs"] == 0
    sample = R["probes"]["sample"]
    assert sample["argv"] == ["/usr/bin/powermetrics", "-s", "cpu_power", "-i", "1000", "-n", "2"]
    assert sample["returncode"] == 1
    assert "must be invoked as the superuser" in sample["stderr"].lower()
    manual_raw = R["probes"]["manual"]["stdout"]
    # `man` uses overstrike sequences (e.g. p\bp) to mark bold/underline text.
    manual = re.sub(r".\x08", "", manual_raw).lower()
    help_text = R["probes"]["help"]["stdout"].lower()
    assert "estimated power" in help_text or "power values reported by powermetrics are estimated" in help_text
    assert "rough proxy" in manual and "per-process energy impact" in manual
    assert "resolution" not in help_text and "joules" not in help_text
    assert R["eligible_energy_counter_found"] is False
    assert R["disposition"] == F["stop_status"] == "HOLD_ENERGY_SENSOR_UNAVAILABLE"
    result = {
        "format": "issue7728-energy-sensor-preflight-audit-v2",
        "base_commit": F["base_commit"],
        "system_binary_hash_matches_freeze": True,
        "candidate_hash_matches_freeze": True,
        "sample_requires_superuser": True,
        "privilege_escalation_used": False,
        "manual_overstrike_normalized": True,
        "power_values_are_documented_estimates": True,
        "process_energy_impact_is_documented_rough_proxy": True,
        "eligible_unprivileged_cumulative_counter_with_domain_unit_resolution": False,
        "later_T0_gates_run": False,
        "v1_auditor_parse_failure_preserved": True,
        "candidate_rerun": False,
        "disposition": "HOLD_ENERGY_SENSOR_UNAVAILABLE",
        "audit_pass": True,
    }
    OUT.write_text(json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n")
    print(json.dumps({"audit_pass": True, "disposition": result["disposition"], "sample_requires_superuser": True}, sort_keys=True))


if __name__ == "__main__":
    main()
