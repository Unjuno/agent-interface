"""Replay positive, negative and limit finish artifacts through outcome selection."""
import json
import tempfile
from pathlib import Path

from persisted_outcome_v1 import select


HERE = Path(__file__).resolve().parent


def refused(root, kind=None):
    try:
        select(root, kind)
    except (FileNotFoundError, ValueError):
        return True
    return False


def main():
    v9 = HERE / "results/timing-envelope-openttd-l-09/fixed-astra"
    v11 = HERE / "results/timing-envelope-openttd-l-11/fixed-astra"
    v8 = HERE / "results/timing-envelope-openttd-l-08/fixed-astra"
    assert select(v9, "visual_verify")[0].name == "result.json"
    assert select(v11, "bounded_turn_limit")[0].name == "result.json"
    assert select(v8)[0].name == "failure-evaluation.json"
    with tempfile.TemporaryDirectory(prefix="persisted-outcome-controls-") as temporary:
        root = Path(temporary)
        assert refused(root)
        (root / "result.json").write_text(json.dumps({"success": False}) + "\n")
        assert refused(root)
        (root / "result.json").write_text(json.dumps({
            "success": True, "finish_kind": "visual_verify"}) + "\n")
        assert refused(root, "bounded_turn_limit")
        (root / "failure-evaluation.json").write_text(json.dumps({
            "success": False, "finish_kind": "visual_verify"}) + "\n")
        assert refused(root, "visual_verify")
        (root / "result.json").unlink()
        (root / "failure-evaluation.json").write_text(json.dumps({
            "success": True, "finish_kind": "visual_verify"}) + "\n")
        assert refused(root, "visual_verify")
    result = {
        "passed": True,
        "archived_visual_success_selected": True,
        "archived_bounded_limit_success_selected": True,
        "archived_independent_failure_selected": True,
        "invalid_controls_refused": 5,
        "scope": "persisted outcome selection and filename/finish-kind consistency; no model or GUI run",
    }
    output = HERE / "results/persisted-outcome-v1-probe.json"
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
