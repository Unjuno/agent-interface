import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from runtime.cli_v1.golden_v3 import adapt_dispatch_result


def main():
    refusal = adapt_dispatch_result({
        "status": "returned",
        "result": {"status": "refused", "error": "STALE_BINDING", "partial_effects": []},
    })
    assert refusal["status"] == "refused"
    assert refusal["program_completed"] is False
    assert refusal["task_success"] is False
    assert refusal["diagnostic"] == "STALE_BINDING"

    partial = adapt_dispatch_result({
        "status": "returned",
        "result": {
            "status": "completed",
            "program_completed": True,
            "task_success": False,
            "partial_effects": ["saved"],
        },
    })
    assert partial["status"] == "partial"
    assert partial["program_completed"] is True
    assert partial["task_success"] is False
    assert partial["partial_effects"] == ["saved"]

    cleanup = adapt_dispatch_result({
        "status": "returned",
        "cleanup_error": "BACKEND_CLOSE_FAILED",
        "result": {"program_completed": True, "task_success": True},
    })
    assert cleanup["status"] == "cleanup_failed"
    assert cleanup["program_completed"] is True
    assert cleanup["task_success"] is False
    assert cleanup["cleanup_error"] == "BACKEND_CLOSE_FAILED"

    success = adapt_dispatch_result({
        "status": "returned",
        "result": {"program_completed": True, "task_success": True},
    })
    assert success["status"] == "success"
    assert success["program_completed"] is True
    assert success["task_success"] is True

    unknown = adapt_dispatch_result({"status": "not-known"})
    assert unknown["status"] == "refused"
    assert unknown["adapter_error"] == "UNKNOWN_STATUS"

    print(json.dumps({
        "status": "PASS_GOLDEN_V3_ADAPTER_P1_FIX_SCOPED",
        "cases": 5,
        "nested_refusal_preserved": True,
        "completion_separated": True,
        "cleanup_completion_preserved": True,
        "authority_grants": 0,
        "model_calls": 0,
        "gui_calls": 0,
        "input_calls": 0,
        "network_calls": 0,
    }, sort_keys=True))

if __name__ == "__main__":
    main()
