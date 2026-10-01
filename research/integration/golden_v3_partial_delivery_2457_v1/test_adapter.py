import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from runtime.cli_v1.golden_v3 import adapt_dispatch_result


def run(delivery, task=True):
    return adapt_dispatch_result({"status": "returned", "delivery": delivery, "result": {"program_completed": True, "task_success": task, "partial_effects": ["saved"] if delivery == "confirmed_partial" else []}}, lifecycle=["dispatch", "effect", "release"])


def main():
    partial = run("confirmed_partial")
    assert partial["status"] == "partial", partial
    assert partial["program_completed"] is True and partial["task_success"] is True, partial
    assert partial["partial_effects"] == ["saved"], partial
    confirmed = run("confirmed")
    assert confirmed["status"] == "success", confirmed
    print(json.dumps({"status": "PASS_CONFIRMED_PARTIAL_NON_SUCCESS", "partial_cases": 1, "confirmed_controls": 1, "model_calls": 0, "gui_calls": 0, "input_calls": 0, "network_calls": 0}, sort_keys=True))


if __name__ == "__main__":
    main()
