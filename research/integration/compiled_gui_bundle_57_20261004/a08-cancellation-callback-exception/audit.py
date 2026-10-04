"""Saved-data checks for A08; does not invoke the adapter or compiled core."""

import hashlib
import json
import sys
from pathlib import Path

PR_COMMIT = "6144a1b0a2c88f5d88ff1fce148381f1f22269e1"
EXPECTED_ADAPTER_SHA256 = "43cd4e614de2cbb95b446b44314c15b5e9ccf711d9134dde8874a05774240e0d"
EXPECTED_CORE_SHA256 = "d22160919ad7fc00d8a1c6e1da3240a316b024738362d714fafa68b772005014"


def main():
    raw_path, audit_path = map(Path, sys.argv[1:3])
    raw = json.loads(raw_path.read_text(encoding="utf-8"))
    assert raw["schema"] == "compiled-form-cancel-callback-exception-a08-v1"
    assert raw["pr_source_commit"] == PR_COMMIT
    assert raw["source_sha256"]["pr_adapter"] == EXPECTED_ADAPTER_SHA256
    assert raw["source_sha256"]["compiled_core"] == EXPECTED_CORE_SHA256
    runner_hash = hashlib.sha256((Path(__file__).parent / "run.py").read_bytes()).hexdigest()
    assert raw["source_sha256"]["runner"] == runner_hash
    adapter_hash = hashlib.sha256((Path(__file__).parent / "ADAPTER_PINNED.py").read_bytes()).hexdigest()
    assert adapter_hash == EXPECTED_ADAPTER_SHA256
    assert raw["callback_checks"] == 4
    assert raw["actions_dispatched"] == ["enter_token"]
    assert len(raw["action_terminal_events"]) == 1
    terminal = raw["action_terminal_events"][0]
    assert terminal["release_verified"] is True
    assert raw["returned_receipt"] is None
    assert raw["propagated_exception"] == "RuntimeError: cancellation source unavailable"
    assert raw["journal_event_names"][-1] == "action_terminal"

    report = {
        "status": "FAIL_CALLBACK_EXCEPTION_DROPS_TYPED_RECEIPT",
        "scope": "source-pinned callback/core test-double counterexample; no GUI/OCR/provider/input/network",
        "raw_sha256": hashlib.sha256(raw_path.read_bytes()).hexdigest(),
        "source_sha256": raw["source_sha256"],
        "assertions": {
            "one_action_completed_and_released": True,
            "no_second_action_dispatched": True,
            "callback_exception_escaped": True,
            "typed_run_receipt_returned": False,
            "live_control_claim": False,
        },
    }
    audit_path.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n",
                          encoding="utf-8")
    print(json.dumps(report, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
