import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))

from runtime.cli_v1.golden_v3 import adapt_dispatch_result


def main():
    nested_runtime_failed = adapt_dispatch_result({
        "status": "returned",
        "result": {
            "status": "runtime_failed",
            "program_completed": False,
            "task_success": False,
            "partial_effects": ["pressed"],
            "error": "BACKEND_INTERRUPTED",
        },
    })
    assert nested_runtime_failed["status"] == "partial"
    assert nested_runtime_failed["native_status"] == "runtime_failed"
    assert nested_runtime_failed["partial_effects"] == ["pressed"]
    assert nested_runtime_failed["diagnostic"] == "BACKEND_INTERRUPTED"

    refusal = adapt_dispatch_result({
        "status": "returned",
        "result": {"status": "refused", "error": "STALE_BINDING"},
    })
    assert refusal["status"] == "refused"
    assert refusal["native_status"] == "refused"
    assert refusal["diagnostic"] == "STALE_BINDING"

    completed_but_unknown_task = adapt_dispatch_result({
        "status": "returned",
        "result": {"status": "completed", "program_completed": True},
    })
    assert completed_but_unknown_task["status"] == "partial"
    assert completed_but_unknown_task["program_completed"] is True
    assert completed_but_unknown_task["task_success"] is None

    cleanup = adapt_dispatch_result({
        "status": "returned",
        "cleanup_error": "BACKEND_CLOSE_FAILED",
        "result": {"status": "completed", "program_completed": True, "task_success": True},
    })
    assert cleanup["status"] == "cleanup_failed"
    assert cleanup["program_completed"] is True
    assert cleanup["task_success"] is False

    unknown = adapt_dispatch_result({"status": "not-known"})
    assert unknown["status"] == "refused"
    assert unknown["adapter_error"] == "UNKNOWN_STATUS"

    print(json.dumps({
        "status": "PASS_GOLDEN_V3_ADAPTER_P2_REBASE_SCOPED",
        "cases": 5,
        "nested_runtime_failed_preserved_as_partial": True,
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
