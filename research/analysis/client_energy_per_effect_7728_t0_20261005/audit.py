#!/usr/bin/env python3
"""Independent check of the retained #7728 sensor eligibility stop record."""
import hashlib
import json
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
    assert hashlib.sha256(Path(__file__).read_bytes()).hexdigest() == F["auditor_sha256"]
    assert R["base_commit"] == F["base_commit"]
    assert R["powermetrics_binary"]["sha256"] == F["powermetrics_sha256"]
    assert R["privilege_escalation_attempted"] is False
    assert R["gui_model_route_or_task_runs"] == 0
    sample = R["probes"]["sample"]
    assert sample["argv"] == ["/usr/bin/powermetrics", "-s", "cpu_power", "-i", "1000", "-n", "2"]
    complete_counter = bool(R["sample_emitted_cumulative_counter_tokens"] and R["sample_emitted_explicit_domain"] and R["sample_emitted_explicit_energy_unit"] and R["sample_emitted_explicit_resolution"])
    assert sample["returncode"] != 0 or not complete_counter
    assert R["eligible_energy_counter_found"] is False
    assert R["disposition"] == F["stop_status"] == "HOLD_ENERGY_SENSOR_UNAVAILABLE"
    manual = R["probes"]["manual"]["stdout"].lower()
    assert R["manual_documents_estimated_power"] is True
    assert R["manual_documents_process_energy_as_rough_proxy"] is True
    assert "may be inaccurate" in manual
    assert "rough proxy" in manual
    audit = {
        "format": "issue7728-energy-sensor-preflight-audit-v1",
        "base_commit": F["base_commit"],
        "candidate_hash_matches_freeze": True,
        "system_binary_hash_matches_freeze": True,
        "non_privileged_probe_only": True,
        "estimated_power_and_process_proxy_are_not_joules": True,
        "eligible_cumulative_counter": False,
        "later_T0_tests_executed": False,
        "disposition": "HOLD_ENERGY_SENSOR_UNAVAILABLE",
        "audit_pass": True,
    }
    OUT.write_text(json.dumps(audit, sort_keys=True, separators=(",", ":")) + "\n")
    print(json.dumps({"audit_pass": True, "disposition": audit["disposition"]}, sort_keys=True))


if __name__ == "__main__":
    main()
