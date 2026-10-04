"""Run the corrected cross-OS authored-condition transfer allocation."""
import hashlib
import json
from pathlib import Path

from run_local_displacement_transfer_v1 import run_case


HERE = Path(__file__).resolve().parent
OUT = HERE / "results/local-displacement-transfer-02"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    plan = json.loads((OUT / "preregistration.json").read_text())
    assert plan["status"] == "preregistered_before_fresh_x11_execution"
    for name, expected in plan["sources"].items():
        assert sha(HERE / name) == expected, name
    authored_source = HERE / plan["authored_source_relative"]
    assert sha(authored_source) == plan["authored_source_sha256"]
    assert sha(OUT / "authored-postcondition.json") == plan["authored_output_sha256"]
    spec = json.loads((OUT / "authored-postcondition.json").read_text())
    assert spec == plan["authored_output"]
    rows = []
    for name in plan["order"]:
        result = run_case(name, plan["allocations"][name], spec, OUT / name)
        rows.append(result)
        (OUT / "execution.json").write_text(json.dumps(rows, indent=2) + "\n")
    passed = all(
        row["observed_visual_delta"] == plan["allocations"][row["name"]]["expected_visual_delta"] and
        row["postcondition"]["reason"] == plan["allocations"][row["name"]]["expected_postcondition"] and
        row["save_started"] is plan["allocations"][row["name"]]["save"] and
        row["terminal"]["release"]["verified"] is True
        for row in rows
    )
    report = {
        "passed": passed, "cases": rows,
        "decision": ("RETAIN_MODEL_AUTHORED_FRESH_TRANSFER;_REPLICATE_BEFORE_PROMOTION"
                     if passed else "HOLD_MODEL_AUTHORED_TRANSFER;_PRESERVE_FAILURE"),
        "scope": plan["interpretation"],
    }
    (OUT / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
