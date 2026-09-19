import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from runtime.cli_v1.golden_v3 import adapt_dispatch_result


def main():
    cases = []
    for location in ("top", "nested"):
        result = {"status": "returned", "result": {"program_completed": True, "task_success": True}}
        if location == "top":
            result["delivery"] = "ambiguous"
        else:
            result["result"]["delivery"] = "write_uncertain"
        row = adapt_dispatch_result(result, lifecycle=["dispatch", "release"])
        assert row["status"] == "refused", row
        assert row["program_completed"] is False, row
        assert row["task_success"] is False, row
        assert row["diagnostic"].startswith("AMBIGUOUS_DELIVERY:"), row
        assert row["raw_dispatch"] == result, row
        cases.append(location)

    success = adapt_dispatch_result(
        {"status": "returned", "result": {"program_completed": True, "task_success": True}},
        lifecycle=["dispatch", "effect", "release"],
    )
    assert success["status"] == "success", success

    print(json.dumps({"status": "PASS_AMBIGUOUS_DELIVERY_FAIL_CLOSED", "cases": cases, "model_calls": 0, "gui_calls": 0, "input_calls": 0, "network_calls": 0}, sort_keys=True))


if __name__ == "__main__":
    main()
