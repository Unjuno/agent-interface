import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from runtime.cli_v1.golden_v3 import adapt_dispatch_result


def row(delivery, nested=False):
    result = {"status": "returned", "result": {"program_completed": True, "task_success": True}}
    if nested:
        result["result"]["delivery"] = delivery
    else:
        result["delivery"] = delivery
    return adapt_dispatch_result(result, lifecycle=["dispatch", "release"])


def main():
    for nested in (False, True):
        x = row("mystery", nested)
        assert x["status"] == "refused", x
        assert x["program_completed"] is False and x["task_success"] is False, x
        assert x["diagnostic"] == "UNKNOWN_DELIVERY:mystery", x
    confirmed = row("confirmed")
    assert confirmed["status"] == "success", confirmed
    partial = row("confirmed_partial")
    assert partial["status"] == "success", partial
    absent = adapt_dispatch_result({"status": "returned", "result": {"program_completed": True, "task_success": True}}, lifecycle=["dispatch"])
    assert absent["status"] == "success", absent
    print(json.dumps({"status": "PASS_UNKNOWN_DELIVERY_FAIL_CLOSED", "unknown_cases": 2, "known_controls": 2, "model_calls": 0, "gui_calls": 0, "input_calls": 0, "network_calls": 0}, sort_keys=True))


if __name__ == "__main__":
    main()
