#!/usr/bin/env python3
"""One-shot, unprivileged host energy-sensor eligibility probe for Issue #7728."""
import hashlib
import json
import os
import platform
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FREEZE = json.loads((ROOT / "FREEZE.json").read_text())
OUT = ROOT / "RESULT.json"


def run(argv, timeout=20):
    try:
        p = subprocess.run(argv, capture_output=True, text=True, timeout=timeout, check=False)
        return {"argv": argv, "returncode": p.returncode, "stdout": p.stdout, "stderr": p.stderr, "timeout": False}
    except subprocess.TimeoutExpired as e:
        return {"argv": argv, "returncode": None, "stdout": e.stdout or "", "stderr": e.stderr or "", "timeout": True}


def main():
    if OUT.exists():
        raise SystemExit("STOP_OUTPUT_EXISTS")
    if subprocess.check_output(["git", "rev-parse", "HEAD"]).decode().strip() != FREEZE["base_commit"]:
        raise SystemExit("STOP_BASE_COMMIT_MISMATCH")
    binary = Path(FREEZE["powermetrics_path"])
    actual_binary_hash = hashlib.sha256(binary.read_bytes()).hexdigest()
    if actual_binary_hash != FREEZE["powermetrics_sha256"]:
        raise SystemExit("STOP_BINARY_HASH_MISMATCH")
    host = {
        "system": platform.system(),
        "release": platform.release(),
        "machine": platform.machine(),
        "macos_product_version": run(["sw_vers", "-productVersion"])["stdout"].strip(),
        "macos_build": run(["sw_vers", "-buildVersion"])["stdout"].strip(),
        "hardware_model": run(["sysctl", "-n", "hw.model"])["stdout"].strip(),
        "hostname_recorded": False,
    }
    help_probe = run(["/usr/bin/powermetrics", "-h"])
    sample_probe = run(["/usr/bin/powermetrics", "-s", "cpu_power", "-i", "1000", "-n", "2"], timeout=10)
    manual = run(["/usr/bin/man", "-P", "cat", "powermetrics"], timeout=15)
    manual_text = manual["stdout"]
    lower = manual_text.lower()
    estimated_power_documented = "estimated power" in lower or "power values are estimated" in lower
    rough_process_proxy_documented = "rough proxy" in lower and "process" in lower
    output = (sample_probe["stdout"] + "\n" + sample_probe["stderr"]).lower()
    cumulative_counter_tokens = [x for x in ("rapl", "cumulative energy", "energy counter", "energy_joules", "energy_uj", "energy_nj") if x in output]
    explicit_domain = any(x in output for x in ("cpu package", "soc package", "package energy", "rapl package"))
    explicit_energy_unit = any(x in output for x in ("joule", " j ", "mj", "uj", "µj", "μj", "nj"))
    explicit_resolution = any(x in output for x in ("resolution", "least significant", "counter quantum", "counter granularity"))
    # powermetrics' process Energy Impact is deliberately not accepted as joules.
    eligible = bool(sample_probe["returncode"] == 0 and cumulative_counter_tokens and explicit_domain and explicit_energy_unit and explicit_resolution)
    result = {
        "format": "issue7728-energy-sensor-preflight-v1",
        "classification": "host-specific unprivileged sensor eligibility probe",
        "base_commit": FREEZE["base_commit"],
        "host": host,
        "powermetrics_binary": {"path": str(binary), "sha256": actual_binary_hash},
        "probes": {"help": help_probe, "sample": sample_probe, "manual": manual},
        "manual_documents_estimated_power": estimated_power_documented,
        "manual_documents_process_energy_as_rough_proxy": rough_process_proxy_documented,
        "sample_emitted_cumulative_counter_tokens": cumulative_counter_tokens,
        "sample_emitted_explicit_domain": explicit_domain,
        "sample_emitted_explicit_energy_unit": explicit_energy_unit,
        "sample_emitted_explicit_resolution": explicit_resolution,
        "eligible_energy_counter_found": eligible,
        "privilege_escalation_attempted": False,
        "gui_model_route_or_task_runs": 0,
        "disposition": "T0_SENSOR_ELIGIBLE" if eligible else "HOLD_ENERGY_SENSOR_UNAVAILABLE",
    }
    OUT.write_text(json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n")
    print(json.dumps({"disposition": result["disposition"], "sample_returncode": sample_probe["returncode"],
                      "eligible_energy_counter_found": eligible}, sort_keys=True))


if __name__ == "__main__":
    main()
