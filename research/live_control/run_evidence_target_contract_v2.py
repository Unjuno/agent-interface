"""Run the frozen local controls and endpoint preflight."""
import json
from pathlib import Path
import subprocess
import sys

from schema_preflight_v1 import preflight

HERE = Path(__file__).resolve().parent
OUT = HERE / "results/evidence-target-contract-v2-01"


def main():
    plan = json.loads((OUT / "preregistration.json").read_text())
    control = subprocess.run([sys.executable, str(HERE / "test_evidence_target_contract_v2.py")], capture_output=True, text=True, check=True)
    (OUT / "local-controls.json").write_text(control.stdout, encoding="utf-8", newline="\n")
    result = preflight(HERE / "evidence_target_contract_schema_v3.json", OUT / "cache",
        OUT / "endpoint-preflight", OUT / "empty-workspace")
    checks = {"local_controls": json.loads(control.stdout)["passed"] is True,
        "endpoint_compatible": result["endpoint_status"] == "ENDPOINT_COMPATIBLE",
        "fresh_call": result["model_call_performed"] is True and result["cache_hit"] is False,
        "usage_recorded": result["usage"] is not None}
    report = {"local_controls": json.loads(control.stdout), "endpoint_preflight": result,
        "checks": checks, "passed": all(checks.values()), "scope": plan["scope"]}
    (OUT / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__": main()
